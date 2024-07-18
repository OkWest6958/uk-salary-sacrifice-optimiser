import streamlit as st
import numpy as np
import numpy_financial as npf
import pandas as pd
import copy



page_title = "Optimising Salary Sacrifice Contributions"


st.set_page_config(
    page_title=page_title,
    page_icon=":money_with_wings:",
    menu_items={
        'Report a Bug': 'mailto:ok_west_6958@proton.me?subject=Issue%20with%20' + page_title.replace(" ","%20") + '%20app'
        }
)



st.write('# '+page_title)



brt_tax_rate = 0.2
hrt_tax_rate = 0.4
brt_ni_rate = 0.08
hrt_ni_rate = 0.02
brt_threshold = 12570.00
hrt_threshold = 50270.00


min_wage_hourly = 11.44
min_wage_yearly = min_wage_hourly * 37.5 * 52
min_wage_monthly = min_wage_yearly / 12



with st.expander('How to use this calculator'):
    st.write('''Because of how National Insurance (NI) is calculated, it is possible 
    to reduce your NI obligation simply by restructuring when you make your pension contributions.
    \nIncome tax from employment is calculated in month by projecting your yearly income, and evenly 
    charging you tax based on the number of months remaining in year. If you have over or underpaid tax 
    in any given tax year, this will be reconciled in future years.
    \nIn contrast, NI is calculated in month for that month only (technically weekly), and is never reconciled. This means if you 
    overpay (relative to your yearly earnings), you are unable to reclaim this money, and if you underpay 
    then you will not be charged.
    \nAs such, by altering the timing of how much you salary sacrifice into your pension, you can pay a minimal 
    amount of NI at the higher Basic Rate Tax (BRT) Band rate ({0:,.0f}%), and as much as possible at the lower Higher Rate 
    Tax (HRT) Band rate ({1:,.0f}%).'''.format(brt_ni_rate * 100 ,hrt_ni_rate * 100))


st.warning(
    """This calculator is still in development. The below calculations are correct (with the exception of 
    the "income tax" field which may at times be inaccurate (this figure is not significant for the calculator)), 
    but it missing some features such as "estimated monthly take home", the ability to target a monthly take home amount, and an assessment of the opportunity 
    cost involved in managing the Sal Sac approach.
    \n\nYour employer will need to allow mid-year pension contributions in order for you to action any of the below.
    \n\nIf you find any errors please use the "raise a bug" feature in the top right menu."""
)

st.divider()

"""# Pension contributions"""


base_yearly_salary = st.number_input(
    'What is your base yearly salary (£)?',
    0.00,
    100000.00,
    75000.00,
    1000.00,
    )

base_monthly_salary = base_yearly_salary / 12

employer_contribution_percentage = st.number_input(
    'What is your maximum **employer** pension contribution (%)?',
    0.00,
    100.00,
    5.00,
    0.50
)

employer_contribution_percentage = employer_contribution_percentage / 100

employee_contribution_percentage = st.number_input(
    'What **employee** contribution is required to get the maximum employer contribution (%)?',
    0.00,
    100.00,
    5.00,
    0.50
)

employee_contribution_percentage = employee_contribution_percentage / 100

employer_contribution = base_yearly_salary * employer_contribution_percentage

employee_contribution = base_yearly_salary * employee_contribution_percentage

employee_contribution_monthly = employee_contribution / 12

min_total_contribution = employee_contribution + employer_contribution

st.write('Your current total pension contributions are :green[£{:,.2f}] per year'.format(min_total_contribution))

target_total_contribution = st.number_input(
    'What is your desired yearly pension contribution (£)?',
    min_total_contribution,
    base_yearly_salary,
    min_total_contribution,
    100.00
)


voluntary_contributions = target_total_contribution - min_total_contribution

total_employee_cont_perc = (voluntary_contributions + employee_contribution) / base_yearly_salary


if base_yearly_salary - target_total_contribution < min_wage_yearly:
    st.error("""You cannot salary sacrifice below minimum wage. Minimum wage is currently £{:,.2f}. 
             The maximum you can salary sacrifice is £{:,.2f}""".format(min_wage_yearly,base_yearly_salary-min_wage_yearly))
    st.stop()


if voluntary_contributions > 0:
    st.write("""You will need to salary sacrifice an additional :green[£{0:,.2f}] to meet 
         your desired target of :green[£{1:,.2f}] a year (:green[£{0:,.2f}] additional contributions, 
         :green[£{2:,.2f}] contributions to get the maximum employer contributions, and :green[£{3:,.2f}]
         employer contributions)
         \nThis is a total {4:,.2f}% employee contribution""".format(voluntary_contributions,target_total_contribution,employee_contribution, employer_contribution,total_employee_cont_perc * 100))
    

months = [
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
    "January",
    "February",
    "March"
]


schedule_df = pd.DataFrame(
    {
        "Month": months,
        "Gross Base Salary": base_monthly_salary,
        "Minimum Wage": min_wage_monthly,
        "Required Salary Sacrifice": employee_contribution_monthly,
        "Voluntary Salary Sacrifice": np.nan,
        "Required Total Employee Pension Contribution": np.nan,
        "Revised Gross Salary": np.nan,
        "Projected Yearly Income": np.nan,
        "Income Tax": np.nan,
        "National Insurance": np.nan
    }
)



remaining_voluntary_contributions = voluntary_contributions
running_tax = 0.00
running_income = 0.00


for i in range(12):
    monthly_voluntary_sal_sac = min(base_monthly_salary - employee_contribution_monthly - min_wage_monthly, remaining_voluntary_contributions)
    remaining_voluntary_contributions -= monthly_voluntary_sal_sac
    schedule_df.iloc[i,schedule_df.columns.get_loc("Voluntary Salary Sacrifice")] = monthly_voluntary_sal_sac

    total_employee_monthly_cont_perc = (monthly_voluntary_sal_sac + employee_contribution_monthly) / base_monthly_salary * 100
    schedule_df.iloc[i,schedule_df.columns.get_loc("Required Total Employee Pension Contribution")] = total_employee_monthly_cont_perc

    revised_gross = base_monthly_salary - employee_contribution_monthly - monthly_voluntary_sal_sac
    schedule_df.iloc[i,schedule_df.columns.get_loc("Revised Gross Salary")] = revised_gross

    projected_income = running_income + revised_gross * (12 - i)
    running_income += revised_gross
    schedule_df.iloc[i,schedule_df.columns.get_loc("Projected Yearly Income")] = projected_income

    hrt_threshold_excess_projected = max(0,projected_income - hrt_threshold)
    hrt_tax = hrt_threshold_excess_projected * hrt_tax_rate
    brt_threshold_excess_projected = max(0,projected_income - hrt_threshold_excess_projected - brt_threshold)
    brt_tax = brt_threshold_excess_projected * brt_tax_rate
    total_tax = hrt_tax + brt_tax
    remaining_tax = total_tax - running_tax
    income_tax = remaining_tax / (12 - i)
    running_tax += income_tax
    schedule_df.iloc[i,schedule_df.columns.get_loc("Income Tax")] = income_tax

    hrt_threshold_excess_actual = max(0,revised_gross * 12 - hrt_threshold)
    hrt_ni = hrt_threshold_excess_actual * hrt_ni_rate
    brt_threshold_excess_actual = max(0,revised_gross * 12 - hrt_threshold_excess_actual - brt_threshold)
    brt_ni = brt_threshold_excess_actual * brt_ni_rate
    total_ni = (hrt_ni + brt_ni) / 12
    schedule_df.iloc[i,schedule_df.columns.get_loc("National Insurance")] = total_ni


total_tax_optimal = schedule_df["Income Tax"].sum()

total_ni_optimal = schedule_df["National Insurance"].sum()


"""# Results"""

gross_yearly_suboptimal = base_yearly_salary - voluntary_contributions - employee_contribution
hrt_threshold_excess_suboptimal = max(0,gross_yearly_suboptimal - hrt_threshold)
brt_threshold_excess_suboptimal = max(0,gross_yearly_suboptimal - hrt_threshold_excess_suboptimal - brt_threshold)
hrt_ni_suboptimal = hrt_threshold_excess_suboptimal * hrt_ni_rate
brt_ni_suboptimal = brt_threshold_excess_suboptimal * brt_ni_rate
total_ni_suboptimal = hrt_ni_suboptimal + brt_ni_suboptimal


st.write("""If you were to set your employee contributions to {0:,.2f}% consistently throughout the year, 
         you would pay a total of £{1:,.2f} NI per year. By optimising your contributions throughout the year, 
         you would instead pay a total of £{2:,.2f} a year
         \nThis is a saving of £{3:,.2f}""".format(total_employee_cont_perc*100, total_ni_suboptimal, total_ni_optimal, total_ni_suboptimal - total_ni_optimal))


schedule_df
