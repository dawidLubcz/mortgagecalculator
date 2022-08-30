import copy
import dataclasses


@dataclasses.dataclass
class ExcessPayment:
    def __init__(self, month_number: int, value: int):
        self._month_number = month_number
        self._value = value

    @property
    def month(self):
        return self._month_number

    @property
    def value(self):
        return self._value

    def __repr__(self):
        return f"month={self.month} value={self.value}"


@dataclasses.dataclass
class CreditParams:
    def __init__(self, additional_capital, percentage):
        self._capital = additional_capital
        self._percentage = percentage

    @property
    def capital(self):
        return self._capital

    @property
    def percentage(self):
        return self._percentage


class CreditParamsUpdate:
    def on_next_installment(self, installment_index, left_to_pay) -> CreditParams:
        pass


class CreditChanges:
    def __init__(self, excess_payments: list, credit_params_callback: CreditParamsUpdate):
        pass


class Mortgage:
    """Class for calculating credit fees allows to simulate and plan credit repayment."""

    def __init__(self, credit_value: float, credit_percentage: float, months: int = 12, credit_commission: int = 0):
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

    def _get_timetable_constant(self, value, pays_num, percent, pays_per_year, excess_payments):
        left_to_pay = value
        constant_installment_value = Mortgage._get_constant_installment_value(value, pays_num, percent, pays_per_year)
        timetable = []
        summary_cost = 0

        for i in range(0, pays_num):
            interest = left_to_pay * percent / pays_per_year
            capital = constant_installment_value - interest
            installment = constant_installment_value

            excess = Mortgage._check_excess_payments(i, excess_payments)
            capital += excess

            summary_cost += capital + interest
            timetable.append((installment, interest, capital, excess))
            left_to_pay -= capital
            if left_to_pay <= 0:
                break
            constant_installment_value = self._get_constant_installment_value(left_to_pay, pays_num - i - 1, percent, pays_per_year)

        return timetable, summary_cost + self._credit_commission

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

    def _get_timetable_decreasing(self, value, pays_num, percent, pays_per_year, excess_payments):
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
            excess = Mortgage._check_excess_payments(i, excess_payments)
            capital += excess
            timetable.append((installment, interest, capital, excess))
            summary_cost += interest + capital
            left_to_pay -= capital
            if excess > 0:
                constant_capital_value = recalculate(left_to_pay, pays_num - i)
            if left_to_pay <= 0:
                break

        return timetable, summary_cost + self._credit_commission

    def get_timetable(self, excess_payments: list = None, constant: bool = True):
        """
        :param excess_payments: list of ExcessPayment objects
        :param constant: constant installment or decreasing installment
        :return: timetable, summary costs
        """
        excess_payments = copy.deepcopy(excess_payments) or []
        Mortgage._prepare_excess_payments(excess_payments)
        if constant:
            return self._get_timetable_constant(
                self._credit_value, self._months, self._credit_percentage, self._pays_per_year, excess_payments)
        else:
            return self._get_timetable_decreasing(
                self._credit_value, self._months, self._credit_percentage, self._pays_per_year, excess_payments)


# example
def main():
    value = 234902
    months = 212
    percent = 0.0347
    commission = 0

    # TODO: Create object for excess payments to accept formulas i.e for each even month add 1000$
    excess_payments = [
        #ExcessPayment(2, 10000)
    ]

    o = Mortgage(credit_value=value, months=months, credit_percentage=percent, credit_commission=commission)
    o1 = Mortgage(credit_value=value, months=months, credit_percentage=percent, credit_commission=commission)
    tt, rv = o.get_timetable(excess_payments, constant=False)
    ttn, rvn = o1.get_timetable(excess_payments, constant=True)

    for i in range(0, len(ttn)):
        if len(tt) <= i:
            r, o, k, n = 0,0,0,0
        else:
            r = tt[i][0]
            o = tt[i][1]
            k = tt[i][2]
            n = tt[i][3]
        print("%d. installment: %s, interest: %s, capital: %s, excess: %s || installment: %s, interest: %s, capital: %s, excess: %s" % (i+1, ttn[i][0], ttn[i][1], ttn[i][2], ttn[i][3], r, o, k, n))
    print("Mortgage value constant: %0.2f, %0.2f" % (rvn, rvn - value))
    print("Mortgage value decreasing: %0.2f, %0.2f" % (rv, rv - value))
    print("Difference: cash=%s, months=%s;%s, years=%s;%s "  % (str(rvn-rv), str(len(ttn)), str(len(tt)), str(len(ttn)/12), str(len(tt)/12)))


if __name__ == '__main__':
    main()
