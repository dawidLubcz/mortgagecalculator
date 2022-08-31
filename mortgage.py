#!/usr/bin/python3

__doc__ = """Script for calculating and simulating credit costs based on input parameters"""


import copy
import dataclasses


@dataclasses.dataclass
class ExcessPayment:
    """Single capital overpayment"""
    def __init__(self, month_number: int, value: int):
        self._month_number = month_number
        self._value = value

    @property
    def month(self):
        """Month on which overpayment should happen"""
        return self._month_number

    @property
    def value(self):
        """Capital value"""
        return self._value

    def __repr__(self):
        return f"month={self.month} value={self.value}"


@dataclasses.dataclass
class CreditParameterUpdate:
    """Type used by CreditParameterUpdateListener.on_installment
    for updating credit parameters i.e. percentage change or capital overpayment"""
    def __init__(self, excess_payment, percentage):
        self._excess_payment = excess_payment
        self._percentage = percentage

    @property
    def excess_payment(self):
        """Capital overpayment getter"""
        return self._excess_payment

    @excess_payment.setter
    def excess_payment(self, excess_payment):
        """Capital overpayment setter"""
        self._excess_payment = excess_payment

    @property
    def percentage(self):
        """Percentage change getter"""
        return self._percentage

    @percentage.setter
    def percentage(self, percent):
        """Percentage change setter"""
        self._percentage = percent


class CreditParameterUpdateListener:
    """Object if this class is used by CreditChanges for listening
    on every installment calculation to be able to apply some formula
    to change credit percentage in time for example"""
    def on_installment(self,
                       installment_index: int,
                       left_to_pay: float,
                       percent: float) -> CreditParameterUpdate:
        """
        This method will be called on each installment calculation.
        :param installment_index: installment number / month - starting from 0
        :param left_to_pay: capital left to pay
        :param percent: current credit percentage
        :return: CreditParameterUpdate, parameters update
        """
        return CreditParameterUpdate(0, percent)


class CreditChanges:
    """Class for managing all credit changes, excess payment, percentage updates etc"""
    def __init__(self,
                 excess_payments: list = None,
                 credit_params_callback: CreditParameterUpdateListener = None):
        self._excess_payments = excess_payments or []
        self._prepare_excess_payments(self._excess_payments)
        self._on_installment_callback = credit_params_callback or CreditParameterUpdateListener()

    @staticmethod
    def _prepare_excess_payments(excess_payments: list):
        def sort_func(item: ExcessPayment):
            return item.month
        excess_payments.sort(key=sort_func)

    @staticmethod
    def _check_excess_payments(payment_month: int, excess_payments):
        excess = 0
        if len(excess_payments) > 0 and excess_payments[0].month - 1 == payment_month:
            excess = excess_payments[0].value
            excess_payments.pop(0)
        return excess

    def get_credit_update(self, installment_index, left_to_pay, percent) -> CreditParameterUpdate:
        """
        Method called by Mortgage class for each installment calculation
        :param installment_index: installment number / month - starting from 0
        :param left_to_pay: capital left to pay
        :param percent: current credit percentage
        :return:
        """
        result = CreditParameterUpdate(0, percent)
        result = self._on_installment_callback.on_installment(
            installment_index, left_to_pay, percent) or result
        result.excess_payment += self._check_excess_payments(
            installment_index, self._excess_payments)
        return result


class Mortgage:
    """Class for calculating credit fees allows to simulate and plan credit repayment."""

    def __init__(self, credit_value: float,
                 credit_percentage: float,
                 months: int = 12,
                 credit_commission: int = 0):
        """
        :param credit_value: credit value - money to be repaid
        :param credit_percentage: credit percentage
        :param months: loan repayment length in months
        :param credit_commission: commission to pay - one time payment
        """
        self._credit_value = credit_value
        self._credit_percentage = credit_percentage
        self._months = months
        self._credit_commission = credit_commission
        self._pays_per_year = 12

    @staticmethod
    def _get_constant_installment_value(value, pays_num, percent, pays_per_year):
        tmp_sum = 0
        for i in range(1, pays_num + 1):
            tmp_sum += (1.00 + percent / pays_per_year) ** -i
        return value / tmp_sum

    def _get_timetable_constant(self, value: float,
                                pays_num: int,
                                percent: float,
                                pays_per_year: int,
                                credit_updates: CreditChanges):
        left_to_pay = value
        constant_installment_value = Mortgage._get_constant_installment_value(
            value, pays_num, percent, pays_per_year)
        timetable = []
        summary_cost = 0

        for i in range(0, pays_num):
            interest = left_to_pay * percent / pays_per_year
            capital = constant_installment_value - interest
            installment = constant_installment_value

            update = credit_updates.get_credit_update(i, left_to_pay, percent)
            excess = update.excess_payment
            percent = update.percentage

            capital += excess
            summary_cost += capital + interest
            timetable.append((installment, interest, capital, excess))
            left_to_pay -= capital
            if left_to_pay <= 0:
                break
            constant_installment_value = self._get_constant_installment_value(
                left_to_pay, pays_num - i - 1, percent, pays_per_year)

        return timetable, summary_cost + self._credit_commission

    def _get_timetable_decreasing(self, value: float,
                                  pays_num: int,
                                  percent: float,
                                  pays_per_year: int,
                                  credit_updates: CreditChanges):

        def recalculate(value_left, payment_number):
            return value_left / payment_number

        left_to_pay = value
        constant_capital_value = recalculate(value, pays_num)
        timetable = []
        summary_cost = 0

        for i in range(0, pays_num):
            interest = left_to_pay * percent / pays_per_year
            capital = constant_capital_value
            installment = constant_capital_value + interest

            update = credit_updates.get_credit_update(i, left_to_pay, percent)
            excess = update.excess_payment
            percent = update.percentage

            capital += excess
            timetable.append((installment, interest, capital, excess))
            summary_cost += interest + capital
            left_to_pay -= capital
            if excess > 0:
                constant_capital_value = recalculate(left_to_pay, pays_num - i)
            if left_to_pay <= 0:
                break

        return timetable, summary_cost + self._credit_commission

    def get_timetable(self, credit_updates: CreditChanges = None, constant: bool = True):
        """
        :param credit_updates: list of ExcessPayment objects
        :param constant: constant installment or decreasing installment
        :return: timetable, summary costs
        """
        credit_updates = copy.deepcopy(credit_updates) or CreditChanges()
        if constant:
            return self._get_timetable_constant(self._credit_value,
                                                self._months,
                                                self._credit_percentage,
                                                self._pays_per_year,
                                                credit_updates)

        return self._get_timetable_decreasing(self._credit_value,
                                              self._months,
                                              self._credit_percentage,
                                              self._pays_per_year,
                                              credit_updates)


def main():
    """Example usage"""

    excess_payments = [
        ExcessPayment(2, 10000),
        ExcessPayment(4, 20000),
    ]

    class CreditParamsUpdateExt(CreditParameterUpdateListener):
        """Custom listener"""
        def on_installment(self,
                           installment_index: int,
                           left_to_pay: float,
                           percent: float) -> CreditParameterUpdate:
            """Example"""
            result = CreditParameterUpdate(0, percent)
            # Example of percentage update
            # if installment_index > 4:
            #     result.percentage = 0.07
            return result
    callback = CreditParamsUpdateExt()
    updates = CreditChanges(excess_payments, credit_params_callback=callback)

    value = 1000000
    months = 360
    percent = 0.04
    commission = 0

    interest_decreasing = Mortgage(credit_value=value, months=months,
                                   credit_percentage=percent, credit_commission=commission)

    time_table_decreasing, real_costs_decreasing = interest_decreasing.get_timetable(
        updates, constant=False)
    time_table_constant, real_value_constant = interest_decreasing.get_timetable(
        updates, constant=True)

    for i in range(0, len(time_table_constant)):
        if len(time_table_decreasing) <= i:
            real_cost_decreasing, interest_decreasing = 0, 0
            capital_decreasing, excess_decreasing = 0, 0
        else:
            real_cost_decreasing = time_table_decreasing[i][0]
            interest_decreasing = time_table_decreasing[i][1]
            capital_decreasing = time_table_decreasing[i][2]
            excess_decreasing = time_table_decreasing[i][3]

        print(
            f"{i+1}. "
            f"installment: {time_table_constant[i][0]:.2f}, interest: {time_table_constant[i][1]:.2f}, "
            f"capital: {time_table_constant[i][2]:.2f}, excess: {time_table_constant[i][3]:.2f} || "
            f"installment: {real_cost_decreasing:.2f}, interest: {interest_decreasing:.2f}, "
            f"capital: {capital_decreasing:.2f}, excess: {excess_decreasing:.2f}")

    print(f"Mortgage value constant: {real_value_constant:.2f}, "
          f"costs: {real_value_constant - value:.2f}")
    print(f"Mortgage value decreasing: {real_costs_decreasing:.2f}, "
          f"costs: {real_costs_decreasing - value:.2f}")
    print(f"Difference: cash={real_value_constant-real_costs_decreasing:.2f}, "
          f"months={len(time_table_constant)};{len(time_table_decreasing)}, "
          f"years={len(time_table_constant)/12:.2f};{len(time_table_decreasing)/12:.2f}")


if __name__ == '__main__':
    main()
