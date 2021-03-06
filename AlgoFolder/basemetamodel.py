# -*- coding: utf-8 -*-
"""OfficialStockPredictor

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1SKoBHaNqOMxfOIOQRpqqVoZTkOZH9NmP
"""

import os
os.environ['CUDA_LAUNCH_BLOCKING'] = "1"

!pip install blitz-bayesian-pytorch
!pip install -e git+git://github.com/vonHacht/yfinance.git@master#egg=yfinance
!pip install quandl
#!pip install optuna
!pip install fracdiff

import pandas as pd
import numpy as np
import torch
import torch.nn as nn
#import optuna
import matplotlib.pyplot as plt
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import MinMaxScaler
import blitz
from blitz.modules import BayesianLSTM
from blitz.modules import BayesianLinear
from blitz.utils import variational_estimator
import yfinance as yf
import quandl
from fracdiff import FracdiffStat,fdiff

!pip install quandl
!pip install pandas-datareader
!pip install --upgrade ta
!pip install -U git+https://github.com/twopirllc/pandas-ta
!pip install nest-asyncio
!pip install -U git+https://github.com/mariostoev/finviz
!pip install git+git://github.com/peerchemist/finta.git
!pip install tiingo
!pip install pandas_ta
!pip install robin_stocks
!pip install alpha_vantage pandas
!pip install finviz

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import pandas_datareader as pdr
import ta
from pandas import DataFrame, Series
import nest_asyncio
nest_asyncio.apply()
import finviz
from finviz.screener import Screener
from finta import TA
import tiingo
from tiingo import TiingoClient
import requests
from datetime import datetime
from statistics import mean,median
import urllib
from urllib.parse import urlencode, quote_plus
import robin_stocks as rs
from datetime import datetime,timedelta,date
from dateutil import parser
from alpha_vantage.timeseries import TimeSeries
import time

def typical_price(data, high_col = 'High', low_col = 'Low', close_col = 'Close'):
    
    data['typical_price'] = (data[high_col] + data[low_col] + data[close_col]) / 3

    return data

#def money_flow(data):
  #data['mfi']=ta.volume.money_flow_index(high=data['High'],low=data['Low'],close=data['Close'],volume=data['Volume'])
  #data=data.join(mfi_df)
  
  #return data


def MA_Selector(ticker):
  
  data=yahooTA(ticker)[-720:]

  plus_length,neg_length,avg_plus_perc,avg_neg_perc=averaging_length(data)


  data['max']=data.iloc[scipy.signal.argrelmax(data['Open'].values,order=round(plus_length+neg_length))[0]]['Close']
  data['min']=data.iloc[scipy.signal.argrelmin(data['Close'].values,order=round(plus_length+neg_length))[0]]['Close']

  error_df=pd.concat([data['max']+data['atr'],data['max']-data['atr'],data['min']+data['atr'],data['min']-data['atr']],axis=1)
  error_df.columns=['top+','top-','bottom+','bottom-']

  periods=list(range(50,300,3))

  ema_series_dict={}
  ema_score_dict={}

  hull_series_dict={}
  hull_score_dict={}

  for period in periods:
    ema_series=ta.trend.ema_indicator(data['Close'],window=period)
    ema_series_dict[str(period)]=ema_series

    hull_series=pandas_ta.hma(data['Close'],length=period)
    hull_series_dict[str(period)]=hull_series

    hull_score=0
    ema_score=0
    
    for idx in range(len(error_df['bottom+'])):
      if ema_series.iloc[idx] <= error_df['bottom+'].iloc[idx] and ema_series.iloc[idx] >=error_df['bottom-'].iloc[idx]:
        ema_score+=1
      
      elif hull_series.iloc[idx] <= error_df['bottom+'].iloc[idx] and hull_series.iloc[idx] >=error_df['bottom-'].iloc[idx]:
        hull_score+=1
      
      else:
        continue
    
    for idx in range(len(error_df['top+'])):
      if ema_series.iloc[idx] <= error_df['top+'].iloc[idx] and ema_series.iloc[idx] >=error_df['top-'].iloc[idx]:
        ema_score+=1
      
      elif hull_series.iloc[idx] <= error_df['top+'].iloc[idx] and hull_series.iloc[idx] >=error_df['top-'].iloc[idx]:
        hull_score+=1
      
      else:
        continue

    ema_score_dict[str(period)]=ema_score
    hull_score_dict[str(period)]=hull_score

    for period in list(hull_score_dict.keys()):
      if int(period) <100:
        hull_score_dict.pop(period)
    
    
  ema_selected_key=max(ema_score_dict,key=ema_score_dict.get)
  hull_selected_key=max(hull_score_dict,key=hull_score_dict.get)

  ema_selected_series=ema_series_dict[ema_selected_key]

  hull_selected_series=hull_series_dict[hull_selected_key]

  return ema_selected_series,hull_selected_series

def yahooTA(ticker):
  global data
  data=pdr.get_data_yahoo(ticker)
  data=data.drop('Adj Close',axis=1)
  data=data.reset_index()
  
  data=typical_price(data) 
  data['mfi']=ta.volume.money_flow_index(high=data['High'],low=data['Low'],close=data['Close'],volume=data['Volume'])
  data['ema200']=ta.trend.ema_indicator(close=data['Close'],window=200)
  data['ema_change']=data['ema200'].pct_change()
  data['cci']=ta.trend.cci(high=data['High'],low=data['Low'],close=data['Close'],window=14)
  data['dpo']=ta.trend.dpo(close=data['Close'],window=14)
  data['high_bb0.382']=ta.volatility.bollinger_hband(close=data['Close'],window=14,window_dev=0.382)
  data['low_bb0.382']=ta.volatility.bollinger_lband(close=data['Close'],window=14,window_dev=0.382)
  data['high_bb2']=ta.volatility.bollinger_hband(close=data['Close'],window=14,window_dev=2)
  data['low_bb2']=ta.volatility.bollinger_lband(close=data['Close'],window=14,window_dev=2)
  data['atr']=ta.volatility.average_true_range(high=data['High'],low=data['Low'],close=data['Close'],window=14)
  #data[['eri_bull','eri_bear']]=pandas_ta.momentum.eri(data['High'],data['Low'],data['Close'],13)
  data['perc_change']=data.Close.pct_change(periods=1)*100
  
  return data

def add_MAs(data):

  hull_series,ema_series=MA_Selector(data)

  data[hull_series.name]=hull_series
  data[ema_series.name]=ema_series


  return data

def Tiingo_Intraday(ticker,resampleFreq): #startDate is in YYYY-MM-DD format

  startDate=(datetime.today()- timedelta(days=90)).strftime('%Y-%m-%d')
  endDate= datetime.today().strftime('%Y-%m-%d')

  headers = {
        'Content-Type': 'application/json',
        'Authorization' : 'Token 31aa155f056b3bfb1f7fb95a004a31effeacfd9d'
        }

  params={
      'startDate':startDate,
      'endDate': endDate,
      'resampleFreq':resampleFreq,
      'columns': 'volume',
  }


  url='https://api.tiingo.com/iex/'+ticker+'/prices?'

  requestResponse = requests.get(url,headers=headers,params=params)

  request_json=requestResponse.json()
  
  request_df=pd.DataFrame()
  for dict in request_json:
    series_dict=pd.Series(dict)
    request_df=request_df.append(series_dict,ignore_index=True)

  for index,timestamp in enumerate(request_df['date']):
    timestamp=timestamp.replace('T',' ')
    request_df.date.iloc[index]=timestamp  

  client = TiingoClient({'api_key': '31aa155f056b3bfb1f7fb95a004a31effeacfd9d'})
  
  No_Vol_Df=client.get_dataframe(tickers=ticker,frequency=resampleFreq,startDate=startDate,endDate=endDate)
  No_Vol_Df=No_Vol_Df.reset_index()

  No_Vol_Df['volume']=0
  With_Vol_Df=No_Vol_Df
  for index,timestamp in enumerate(request_df.date):
    With_Vol_Df.volume[With_Vol_Df.date==timestamp[:16]]=request_df.volume.iloc[index]

  With_Vol_Df.columns=[column.title() for column in With_Vol_Df.columns]
  data=With_Vol_Df
  
  data=typical_price(data) 
  data['mfi']=ta.volume.money_flow_index(high=data['High'],low=data['Low'],close=data['Close'],volume=data['Volume'])
  data['ema200']=ta.trend.ema_indicator(close=data['Close'],window=200)
  data['ema_change']=data['ema200'].pct_change()
  data['cci']=ta.trend.cci(high=data['High'],low=data['Low'],close=data['Close'],window=14)
  data['dpo']=ta.trend.dpo(close=data['Close'],window=14)
  data['high_bb0.382']=ta.volatility.bollinger_hband(close=data['Close'],window=14,window_dev=0.382)
  data['low_bb0.382']=ta.volatility.bollinger_lband(close=data['Close'],window=14,window_dev=0.382)
  data['high_bb2']=ta.volatility.bollinger_hband(close=data['Close'],window=14,window_dev=2)
  data['low_bb2']=ta.volatility.bollinger_lband(close=data['Close'],window=14,window_dev=2)
  data['atr']=ta.volatility.average_true_range(high=data['High'],low=data['Low'],close=data['Close'],window=14)

  data.index=data.Date
  data=data.drop('Date',axis=1)
  
  return data

def Alpha_Intraday(ticker,resampleFreq): #resampleFreq has a max of '60min'

  ts=TimeSeries(key='72IAWM28UYUWC2PF',output_format='pandas')

  data,info=ts.get_intraday(ticker,interval=resampleFreq)

  data.columns=['Open','High','Low','Close','Volume']

  return data

def TickerList(url):

  screener=Screener.init_from_url(url)
  screener_dict=screener.get_ticker_details()

  ticker_list=[]
  for dictionary in screener_dict:
    ticker=dictionary['Ticker']
    ticker_list.append(ticker)
  
  return ticker_list

def Mult_TimeFrame(ticker):
  timeless_df=yahooTA(ticker)
  timeless_df.index=timeless_df.Date
  timeless_df=timeless_df.drop('Date',axis=1)
  
  time_list=['720min','359min','239min','120min','60min','30min','5min']
  
  for time in time_list:
    time_df=Tiingo_Intraday(ticker,time)
    time_df.columns=time_df.columns+'_'+time
    timeless_df=pd.merge_asof(timeless_df,time_df,right_index=True,left_index=True)
  
  timeless_df.drop(timeless_df.columns[np.where(timeless_df.isnull().sum()>(0.25*len(timeless_df)))[0]],axis=1)
  timeless_df=timeless_df.fillna(method='bfill')
  timeless_df=timeless_df.loc[:,(timeless_df != timeless_df.iloc[0]).any()] 

  return timeless_df

"""#### Pick Device"""

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print(device)

#parameters
sample_len=25
num_epochs=210

def Stockloader(stock_symbol,period):
  pre_data=Tiingo_Intraday(stock_symbol,'15min').dropna()
  
  labels=pre_data.columns
  scaler=MinMaxScaler(feature_range=(-1,1))
  scaled_data=scaler.fit_transform(pre_data)
  data=pd.DataFrame(scaled_data,columns=labels)
  indices=data.index
  cols=data.columns
  
  return data, scaler, pre_data

"""Defining all functions"""
"""def Stockloader(stock_symbol,period): 
    orig_data=yf.Ticker(stock_symbol).history(period=period,prepost=True)
    info=yf.Ticker(stock_symbol).info

    start_date=str(orig_data.index[0])[0:10]
    end_date=str(orig_data.index[-1])[0:10]

    quandl.ApiConfig.api_key = '7-VJ9UUtktHtEh1iuCaS'
    ShortInts1=quandl.get('FINRA/FNYX_'+stock_symbol,  start_date=start_date, end_date=end_date,column_index='1') #quandl short-interest data
    ShortInts2=quandl.get('FINRA/FNSQ_'+stock_symbol,  start_date=start_date, end_date=end_date,column_index='1')
    ShortInts=ShortInts1+ShortInts2

    pre_data=orig_data.join(ShortInts)
    nan_dates=pre_data.loc[pd.isnull(pre_data).any(axis=1)]['ShortVolume'].index
    
    if len(nan_dates) >0:
      nan_dates=nan_dates.delete(-1) #we don't count the last date as Nan since it has incomplete info
      pre_data.ShortVolume[-1]=info['sharesShort']

    pre_data.ShortVolume=pre_data.ShortVolume.fillna(pre_data.ShortVolume.mean())
    
    for date in nan_dates:
      index=pre_data.index.get_loc(date)
      pre_data['ShortVolume'].iloc[index]= (pre_data['ShortVolume'].iloc[index-1]+pre_data['ShortVolume'].iloc[index+1])/2
  
    pre_data=pre_data.drop(['Dividends','Stock Splits'],axis=1)
    pre_data=(pre_data.iloc[3:].reset_index(drop=True)).divide(pre_data.iloc[:-3].reset_index(drop=True))
    #pre_data=pre_data.pct_change().dropna()
  
    pre_data.Volume[pre_data.Volume==float('inf')]=-1
    pre_data.Volume[pre_data.Volume==-1]=max(pre_data.Volume) 
      
    labels=pre_data.columns
    scaler=MinMaxScaler(feature_range=(-1,1))
    scaled_data=scaler.fit_transform(pre_data)
    data=pd.DataFrame(scaled_data,columns=labels)
    indices=data.index
    cols=data.columns

    f = FracdiffStat()
    data = f.fit_transform(data.values)
    data=pd.DataFrame(data,columns=cols,index=indices)
    
    return data, scaler, pre_data"""

def Extract_XY(data,train_ratio):
    chunk_list=[]

    num_targets=len(data)-sample_len

    for timestep in range(num_targets):
        end_index=timestep+sample_len+1 #targets are only '1' index ahead of inputs
        chunk_list.append(data.iloc[timestep:end_index,:].values)

    chunks=np.array(chunk_list)

    train_data=chunks[:round(train_ratio*data.shape[0])]
    test_data=chunks[round(train_ratio*data.shape[0]):]

    train_inputs=train_data[:,:-1,:]
    train_targets=train_data[:][:,1:,:]

    test_inputs=test_data[:][:,:-1,:]
    test_targets=test_data[:][:,1:,:]

    return train_inputs,train_targets, test_inputs, test_targets

def Tensify(data,train_ratio):
    tensor_list=[]
    train_inputs, train_targets, test_inputs, test_targets = Extract_XY(data,train_ratio)
    
    data_list=[train_inputs,train_targets,test_inputs,test_targets]
    
    for data in data_list:
        tensor_list.append(torch.Tensor(data)) 
        
    train_inputs=tensor_list[0]
    train_targets=tensor_list[1]
    test_inputs=tensor_list[2]
    test_targets=tensor_list[3]
    
    return train_inputs,train_targets,test_inputs,test_targets

def train_step(inputs, targets):
    model.zero_grad()
    output=model(inputs)
    loss = loss_func(output,targets)
    
    loss.backward()#(retain_graph=True)
    optimizer.step()
    
    avg_loss=loss/sample_len
    return avg_loss,output

def eval_step(inputs,targets):
    model.eval()
    evals= model(inputs)
    loss=loss_func(evals,targets)
    avg_loss=loss/sample_len/len(targets)
    return evals, avg_loss

def SpaceFunctionTuner(trial):
  learning_rate=trial.suggest_float('learning_rate',0.01,0.05)
  hidden_size= trial.suggest_int('hidden_size',1,120)
  dropout=trial.suggest_float('dropout',0.02,0.5)
  weight_decay= trial.suggest_uniform('weight_decay',0.001, 0.05)
  global model
  model=net(hidden_size,dropout)
  model.to(device)
  global loss_func
  loss_func = nn.MSELoss()
  global optimizer
  optimizer  = torch.optim.Adam(model.parameters(), lr=learning_rate,weight_decay=weight_decay)
  for epoch in range(num_epochs):
      avg_loss,output=train_step(train_inputs,train_targets)

  evals, eval_loss=eval_step(test_inputs,test_targets) 
  return eval_loss.item()

def hypertune(SpaceFunctionTuner,direction,n_trials):
  study = optuna.create_study(direction=direction,sampler=optuna.samplers.TPESampler(),pruner=optuna.pruners.HyperbandPruner(min_resource=1,max_resource=100,reduction_factor=3))            
  study.optimize(SpaceFunctionTuner, n_trials=n_trials)
  return study.best_trial.params

def ReEvaluate_step(params):
  global model,loss_func,optimizer
  model=net(params['hidden_size'],params['dropout'])
  model.to(device)
  loss_func = nn.MSELoss()
  optimizer  = torch.optim.Adam(model.parameters(), lr=params['learning_rate'],weight_decay=params['weight_decay'])

  global train_losses
  train_losses=[]
  loss_sum=0
  for epoch in range(num_epochs):
      avg_loss,output=train_step(train_inputs,train_targets)
      loss_sum+=avg_loss
      if (epoch % 5) == 4: 
          train_losses.append(loss_sum/5)
          loss_sum=0
  
  global evals, eval_loss
  evals, eval_loss=eval_step(test_inputs,test_targets)

  plt.plot(train_losses)
  plt.title('Training Loss Over Epochs')
  plt.xlabel('Epoch')
  plt.ylabel('Loss')

  plt.title('Training Predictions vs Actual for'+ ' ' + stock_symbol)
  plt.plot(output[:,-1,high_ind].cpu().detach().numpy()[-50:], label="Predicted")
  plt.plot(train_targets[:,-1,high_ind].cpu().detach().numpy()[-50:],label='Actual')
  plt.ylabel('High')
  plt.xlabel('Timestep')
  plt.legend()
  plt.show()

  plt.title('Test Predictions vs. Actual for' + ' ' + stock_symbol)
  plt.plot(evals[:,-1,high_ind].cpu().detach().numpy()[-50:], 'g',label='Predicted')
  plt.plot(test_targets[:,-1,high_ind].cpu().detach().numpy()[-50:],'r',label='Actual')
  plt.ylabel('Close')
  plt.xlabel('Day')
  plt.legend()
  plt.show()

  return output,evals,train_targets,test_targets
  
def StockPredictor(data):
  pred_list=[]

  retrain_inputs=torch.Tensor(data[-sample_len:].values).to(device)

  for timestep in range(sample_len):
      pred_list.append(retrain_inputs[timestep,:].cpu().numpy()) #add to list for easier concat

  
  current_window=torch.Tensor(pred_list[-sample_len:]).view(-1,retrain_inputs.shape[0],retrain_inputs.shape[1]).to(device) #chunks of timesteps

  pred=model(current_window)

  pred_list.append(pred[:,-1,:].view(pred.shape[-1]).cpu().detach().numpy())

          
  #preds=torch.Tensor(pred_list[sample_len:])
  pred=torch.Tensor(pred_list)
  rescaled_pred=scaler.inverse_transform(pred)

  high=rescaled_pred[:,high_ind]
  low=rescaled_pred[:,low_ind]
  close=rescaled_pred[:,close_ind]


  high_delta=100*(rescaled_pred[-1,high_ind]- rescaled_pred[-2,high_ind])/(rescaled_pred[-2,high_ind]) 

  print('Average Error is',eval_loss.item())

  print('Estimated change for',stock_symbol, 'is about',high_delta,'%')

  print('-'*20)  
  
  plt.title('Stock Forecast for'+ ' '+ stock_symbol)
  plt.plot(high)
  plt.ylabel(data.columns[high_ind])
  plt.xlabel('Day') 
  return high_delta

#defining the neural net
@variational_estimator
class net(nn.Module):
    def __init__(self,hidden_size,dropout,batch_first=True):#batch_first=True
        super(net,self).__init__()
        self.hidden_size=hidden_size
      
        self.input_size=train_inputs.shape[2] #number of features
        self.output_size= self.input_size #should = input_size, but change to 1 if we're interested in only 1 feature
        
        self.dropout=nn.Dropout(dropout)
        self.lstm=BayesianLSTM(self.input_size,self.hidden_size)
        #self.linear=BayesianLinear(self.hidden_size,self.output_size)
        self.linear=nn.Linear(self.hidden_size,self.output_size)
    
    def forward(self, inputs):
        output, (hidden,cell) =self.lstm(inputs)
        output=self.dropout(output)
        output= self.linear(output) 
        return output

def StockFunction():
  string=input()
  stock_list=string.split(',')
  
  per_list=['5y']
  prediction_list=[]
  for ticker in stock_list:
    for period in per_list:
      for times in range(2):
        global stock_symbol
        stock_symbol=ticker
        try:
    
          global data,scaler,pre_data
          data,scaler,pre_data=Stockloader(stock_symbol,period)
          global high_ind,low_ind,close_ind
          high_ind= data.columns.get_loc('High')
          low_ind=data.columns.get_loc('Low')
          close_ind=data.columns.get_loc('Close')
          
          global train_inputs,train_targets,test_inputs,test_targets
          train_inputs, train_targets, test_inputs, test_targets=Tensify(data,train_ratio=0.8)
          train_inputs,train_targets,test_inputs,test_targets=train_inputs.to(device),train_targets.to(device),test_inputs.to(device),test_targets.to(device)
          
          #best_params=hypertune(SpaceFunctionTuner,'minimize',50)
          best_params={'dropout': 0.1806872822253523,'hidden_size': 100,'learning_rate': 0.01417891402576243,'weight_decay': 0.0010242338027783872}

          output,evals,train_targets,test_targets=ReEvaluate_step(best_params)

          high_delta=StockPredictor(data)
          prediction_list.append([period, stock_symbol + ' change: '  + str(high_delta)+ ' % | error: ' + str(eval_loss.item())])

        except (KeyError,IndexError,TypeError):
          pass
  
  return prediction_list,evals,test_targets

#aapl,tsla,mitk,gldm,leu,mp,amkr,gme

prediction_list,evals,test_targets=StockFunction()
