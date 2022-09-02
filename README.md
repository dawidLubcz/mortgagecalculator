# mortgagecalculator
Python script for calculating (and simulating) monthly payments of any loan like mortgage for example.

## Script arguments:
- -v / --value ;    credit value 
- -p / --percentage ;   interest rate
- -l / --length ;    loan term - in months
- -c / --commission ;   credit commission
- -t / --credittype ;   equal or decreasing installments
- -e / --excesspayments ;   additional capital
- plt / --plots ; draw plots (matplotlib required)

## Usage
### Equal installment
<code>python3.8 mortgage.py -v 20000 -p 0.04 -l 5 -t 0</code>

Output

```
Loan installments:
        1. installment: 4040.09, interest: 66.67, capital: 3973.42, excess: 0.00
        2. installment: 4040.09, interest: 53.42, capital: 3986.67, excess: 0.00
        3. installment: 4040.09, interest: 40.13, capital: 3999.96, excess: 0.00
        4. installment: 4040.09, interest: 26.80, capital: 4013.29, excess: 0.00
        5. installment: 4040.09, interest: 13.42, capital: 4026.67, excess: 0.00
(...)
  Calculation:
   - Loan real value: 20200.44
   - Costs: 200.44
   - Fees vs value percent=1.00
```

### Decreasing installment
<code>python3.8 mortgage.py -v 20000 -p 0.04 -l 5 -t 1</code>

Output
```
Loan installments:
        1. installment: 4066.67, interest: 66.67, capital: 4000.00, excess: 0.00
        2. installment: 4053.33, interest: 53.33, capital: 4000.00, excess: 0.00
        3. installment: 4040.00, interest: 40.00, capital: 4000.00, excess: 0.00
        4. installment: 4026.67, interest: 26.67, capital: 4000.00, excess: 0.00
        5. installment: 4013.33, interest: 13.33, capital: 4000.00, excess: 0.00
(...)
  Calculation:
   - Loan real value: 20200.00
   - Costs: 200.00
   - Fees vs value percent=1.00
```

### Using switch -plt / --plots you can draw installment schedule:

![image](https://user-images.githubusercontent.com/10208663/188223095-cd6a874e-f5ee-4395-8f90-ad7704fa8af5.png)
![image](https://user-images.githubusercontent.com/10208663/188223210-b4901f52-2290-482b-b20a-25a35b2ac7a8.png)

