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


class Mortgage:
    def __init__(self, credit_value: float, credit_percentage: float, months: int, credit_commission:int=0):
        self._credit_value = credit_value
        self._credit_percentage = credit_percentage
        self._months = months
        self._credit_commission = credit_commission
        self._pays_per_year = 12

    @staticmethod
    def _get_installment(value, pays_num, percent, pays_per_year):
        sum = 0
        for i in range(1, pays_num + 1):
            sum += (1.00 + percent / pays_per_year) ** -i
        return value / sum

    def _get_timetable_constant(self, value, pays_num, percent, pays_per_year, excess_payments, recalculate):
        to_pay = value
        constant_installment = Mortgage._get_installment(value, pays_num, percent, pays_per_year)
        timetable = []
        real_value = 0

        for i in range(0, pays_num):
            interest = to_pay * percent / pays_per_year
            capital = constant_installment - interest
            installment = constant_installment

            excess = Mortgage._check_excess_payments(i, excess_payments)
            capital += excess

            real_value += capital + interest
            timetable.append((installment, interest, capital, excess))
            to_pay -= capital
            if to_pay <= 0:
                break
            if recalculate:
                constant_installment = self._get_installment(to_pay, pays_num - i - 1, percent, pays_per_year)

        return timetable, real_value + self._credit_commission

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

    def _get_timetable_decreasing(self, value, pays_num, percent, pays_per_year, excess_payments, recalculate ="TODO"):
        def recalculate(value_left, payment_number):
            return value_left / payment_number

        to_pay = value
        constant_capital = recalculate(value, pays_num)
        timetable = []
        real_value = 0

        for i in range(0, pays_num):
            interest = to_pay * percent / pays_per_year
            capital = constant_capital
            installment = constant_capital + interest
            excess = Mortgage._check_excess_payments(i, excess_payments)
            capital += excess
            timetable.append((installment, interest, capital, excess))
            real_value += interest + capital
            to_pay -= capital
            if excess > 0:
                constant_capital = recalculate(to_pay, pays_num - i)
            if to_pay <= 0:
                break

        return timetable, real_value + self._credit_commission

    def get_timetable(self, excess_payments: list = None, constant: bool = True, recalculate: bool = False):
        """
        :param excess_payments: [[month, value], [month, value]...]
        :param constant: [True if fixed installment ]
        :param recalculate: [TODO ]
        :return: timetable, mortgage value
        """
        excess_payments = copy.deepcopy(excess_payments) or []
        Mortgage._prepare_excess_payments(excess_payments)
        if constant:
            return self._get_timetable_constant(
                self._credit_value, self._months, self._credit_percentage, self._pays_per_year, excess_payments, recalculate)
        else:
            return self._get_timetable_decreasing(
                self._credit_value, self._months, self._credit_percentage, self._pays_per_year, excess_payments, recalculate)


# example
def main():
    value = 234902
    months = 212
    percent = 0.0347
    commission = 0

    # TODO: Create object for excess payments to accept formulas i.e for each even month add 1000$
    excess_payments = [
        ExcessPayment(2, 10000)
    ]

    o = Mortgage(credit_value=value, months=months, credit_percentage=percent, credit_commission=commission)
    o1 = Mortgage(credit_value=value, months=months, credit_percentage=percent, credit_commission=commission)
    tt, rv = o.get_timetable(excess_payments, constant=False, recalculate=True)
    ttn, rvn = o1.get_timetable(excess_payments, constant=True, recalculate=True)

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
