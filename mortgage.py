#!/usr/bin/python3

__doc__ = """Script for calculating and simulating credit costs based on input parameters"""


import copy
import dataclasses
import argparse
import re


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


class Credit:
    """Class for calculating credit fees allows to simulate and plan credit repayment."""

    def __init__(self, credit_value: float,
                 credit_percentage: float,
                 months: int = 12,
                 credit_commission: float = 0):
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
        constant_installment_value = Credit._get_constant_installment_value(
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
            payment_number = payment_number > 0 and payment_number or 1
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
                constant_capital_value = recalculate(left_to_pay, pays_num - i - 1)
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


class UserInput:
    """Class which represents user input."""

    class CreditType:
        """Enum for credit types."""
        CONSTANT = 0
        DECREASING = 1

    @staticmethod
    def _extract_excess_payments(user_input):
        pattern = re.compile(r"\((\d+),\s*(\d+)\)")
        result = []
        for excess_payment in pattern.findall(user_input):
            result.append(ExcessPayment(
                month_number=int(excess_payment[0]),
                value=int(excess_payment[1])))
        return result

    def __init__(self, argument_parser):
        credit_type_map = {
            "0": UserInput.CreditType.CONSTANT,
            "1": UserInput.CreditType.DECREASING
        }

        self._value = float(argument_parser.value)
        self._percentage = float(argument_parser.percentage)
        self._length = int(argument_parser.length)
        self._commission = float(argument_parser.commission)

        self._credit_type = UserInput.CreditType.CONSTANT
        if argument_parser.credittype in credit_type_map:
            self._credit_type = credit_type_map[argument_parser.credittype]

        self._excess_payments = UserInput._extract_excess_payments(argument_parser.excesspayments)

    @property
    def value(self):
        """Credit value/money"""
        return self._value

    @property
    def percentage(self):
        """The interest rate on the loan."""
        return self._percentage

    @property
    def length(self):
        """Credit length in months."""
        return self._length

    @property
    def commission(self):
        """Credit commission."""
        return self._commission

    @property
    def credit_type(self):
        """Equal or decreasing installments."""
        return self._credit_type

    @property
    def excess_payments(self):
        """Excess payments."""
        return self._excess_payments


def _setup_arguments():
    """Console api"""
    parser = argparse.ArgumentParser(description='Calculate credit installments.')
    parser.add_argument('-v', '--value',
                        help='Credit value.',
                        default=1000000,
                        required=False)
    parser.add_argument('-p', '--percentage',
                        help='The interest rate on the loan.',
                        default=0.04,
                        required=False)
    parser.add_argument('-l', '--length',
                        help='Credit length in months.',
                        default=30*12,
                        required=False)
    parser.add_argument('-c', '--commission',
                        help='Credit commission.',
                        default=0,
                        required=False)
    parser.add_argument('-t', '--credittype',
                        help='Credit type: 0-constant, 1-decreasing',
                        default="0",
                        required=False)
    parser.add_argument('-e', '--excesspayments',
                        help='Excess payments - format:(1,1000)(5,1000)',
                        default="",
                        required=False)
    return parser.parse_args()


def main():
    """Example usage"""
    user_input = UserInput(_setup_arguments())

    print(f"Input=[value={user_input.value}, months={user_input.length}, "
          f"percentage={user_input.percentage}, commission={user_input.commission}, "
          f"excess_payments={user_input.excess_payments}]")

    credit_object = Credit(
        credit_value=user_input.value,
        months=user_input.length,
        credit_percentage=user_input.percentage,
        credit_commission=user_input.commission)

    updates = CreditChanges(excess_payments=user_input.excess_payments)
    time_table, real_value = credit_object.get_timetable(
        updates, constant=user_input.credit_type == UserInput.CreditType.CONSTANT)

    print("\nLoan installments:")
    for i, installment_data in enumerate(time_table):
        installment = installment_data[0]
        interest = installment_data[1]
        capital = installment_data[2]
        excess = installment_data[3]

        print(f"\t{i+1}. "
              f"installment: {installment:.2f}, interest: {interest:.2f}, "
              f"capital: {capital:.2f}, excess: {excess:.2f}")

    print(f"""
Summary:
  Input:
   - value={user_input.value}
   - months={user_input.length}
   - percentage={user_input.percentage}
   - commission={user_input.commission}
   - excess_payments={user_input.excess_payments}

  Calculation:
   - Loan real value: {real_value:.2f}
   - Costs: {real_value - user_input.value:.2f}
   - Fees vs value percent={(real_value - user_input.value)/user_input.value*100:.2f}
""")


if __name__ == '__main__':
    main()
