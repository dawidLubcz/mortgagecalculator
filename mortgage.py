class Mortgage:
    def __init__(self, value, percent, years, commission = 0):
        self.mValue = value
        self.mPercent = percent
        self.mPaysPerYear = 12
        self.mPaysNum = years * self.mPaysPerYear
        self.mCommision = commission

    def __getInstallment(self, value, paysNum, percent, paysPerYear):
        sum  = 0
        for i in range(1, paysNum + 1):
            sum += (1.00 + percent / paysPerYear) ** -i
        return value / sum

    def __getTimetableConstant(self, value, paysNum, percent, paysPerYear, excessPayments, recalculate):
        toPay = value
        constantInstallment = self.__getInstallment(value, paysNum, percent, paysPerYear)
        timetable = []
        realValue = 0

        excessPaymentsCount = len(excessPayments)
        excessPaymentUse = excessPaymentsCount > 0 and excessPayments[0][0] > 0
        excessPaymentsIndex = 0

        for i in range(0, paysNum):
            interest = toPay * percent / paysPerYear
            capital = constantInstallment - interest
            installment = constantInstallment
            excess = 0

            #excess payments
            if excessPaymentUse and i == excessPayments[excessPaymentsIndex][0] - 1:
                excess = excessPayments[excessPaymentsIndex][1]
                excessPaymentsIndex += 1
                if excessPaymentsIndex >= excessPaymentsCount:
                    excessPaymentUse = False

            capital += excess
            realValue += capital + interest
            timetable.append((installment, interest, capital, excess))
            toPay -= capital
            if toPay <= 0:
                break
            if recalculate:
                constantInstallment = self.__getInstallment(toPay, paysNum - i - 1, percent, paysPerYear)

        return timetable, realValue + self.mCommision

    def __getTimetableDecreasing(self, value, paysNum, percent, paysPerYear, excessPayments, recalculate = "TODO"):
        toPay = value
        constantCapital = value / paysNum
        timetable = []
        realValue = 0

        excessPaymentsCount = len(excessPayments)
        excessPaymentUse = excessPaymentsCount > 0 and excessPayments[0][0] > 0
        excessPaymentsIndex = 0

        for i in range(0, paysNum):
            interest = toPay * percent / paysPerYear
            capital = constantCapital
            installment = constantCapital + interest
            excess = 0

            #excess payments
            if excessPaymentUse and i == excessPayments[excessPaymentsIndex][0] - 1:
                excess = excessPayments[excessPaymentsIndex][1]
                excessPaymentsIndex += 1
                if excessPaymentsIndex >= excessPaymentsCount:
                    excessPaymentUse = False

            capital += excess
            timetable.append((installment, interest, capital, excess))
            realValue += interest + capital
            toPay -= capital
            if toPay <= 0:
                break

        return timetable, realValue + self.mCommision

    def getTimetable(self, excessPayments = [], constant = True, recalculate = False):
        '''
        :param excessPayments: [[month, value], [month, value]...]
        :param constant: [True if fixed installment ]
        :return: timetable, mortgage value
        '''
        if constant:
            return self.__getTimetableConstant(
                self.mValue, self.mPaysNum, self.mPercent, self.mPaysPerYear, excessPayments, recalculate)
        else:
            return self.__getTimetableDecreasing(
                self.mValue, self.mPaysNum, self.mPercent, self.mPaysPerYear, excessPayments, recalculate)

#example
def main():
    value = 300000
    years = 20
    percent = 0.045
    commission = 0

    excess = []
    for i in range(0, 20 * 12): # first year 1k per month
        excess.append([i + 1, 1000])
   # offset = len(excess)
    #for i in range(0 + offset, offset + (1 * 12)):  # second year 2k per month
        #excess.append([i + 1, 2000])

    o = Mortgage(value=value, years=years, percent=percent, commission=commission)
    tt, rv = o.getTimetable(excess, constant=False, recalculate=True)
    ttn, rvn = o.getTimetable(constant=False, recalculate=True)

    for i in range(0, len(ttn)):
        if len(tt) <= i:
            r, o, k, n = 0,0,0,0
        else:
            r = tt[i][0]
            o = tt[i][1]
            k = tt[i][2]
            n = tt[i][3]
        print("%d. installment: %s, interest: %s, capital: %s, excess: %s || installment: %s, interest: %s, capital: %s, excess: %s" % (i+1, ttn[i][0], ttn[i][1], ttn[i][2], ttn[i][3], r, o, k, n))
    print("Mortgage value 1: " + str(rvn))
    print("Mortgage value 2: " + str(rv))
    print("Difference: cash=%s, months=%s;%s, years=%s;%s "  % (str(rvn-rv), str(len(ttn)), str(len(tt)), str(len(ttn)/12), str(len(tt)/12)))

if __name__ == '__main__':
    main()