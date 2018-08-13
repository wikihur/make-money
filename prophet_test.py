import pandas as pd
from fbprophet import Prophet

df = pd.read_csv('C:/Users/user/Desktop/Data/test_data_edit.csv')

m_hynix = Prophet(changepoint_prior_scale=0.01).fit(df)

future = m_hynix.make_future_dataframe(periods=9, freq='H')

forecast = m_hynix.predict(future)

m_hynix.plot(forecast)