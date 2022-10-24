# -*- coding: utf-8 -*-
"""Streamlit_app.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1Gv3hM0Y86r5vfq9EAKr1r2N_Y6HaIUqe
"""

#Streamlit Deployment code for ML Model
import streamlit as st
import tensorflow as tf
import pandas as pd
import pickle
from tensorflow import keras
import numpy as np
import time
from PIL import Image

st.title("Water Pumps Status Prediction")
image = Image.open('hand_pump_diagram.jpg')
st.image(image, caption='Water Pumps Status')

st.text('This app will predict Funtional status of Water Pumps')
st.text('You can upload the data below :')

col1,col2 = st.columns(2)
data = col1.file_uploader('Upload the csv file below',type=['csv'])

col1,col2 = st.columns(2)
predict_button = col1.button('Predict on uploaded files')
test_data = col2.button('Predict on sample data')


def data_cleaning(X):
  #Cleaning funder feature
  X['funder'] = X['funder'] .str.replace(' ','_')
  X['funder']= X['funder'] .str.replace('-','_')
  X['funder'] = X['funder'].str.replace(' The ','')
  X['funder'] = X['funder'].str.replace(' ','')
  X['funder'] = X['funder'].str.replace('&','_')
  X['funder'] = X['funder'].str.replace(',','_')
  X['funder'] = X['funder'] .str.lower()

  #Cleaning installer feature
  X['installer'] = X['installer'] .str.replace(' ','_')
  X['installer']= X['installer'] .str.replace('-','_')
  X['installer'] = X['installer'].str.replace(' The ','')
  X['installer'] = X['installer'].str.replace(' ','')
  X['installer'] = X['installer'].str.replace('&','_')
  X['installer'] = X['installer'].str.replace(',','_')
  X['installer'] = X['installer'] .str.lower()

  #cleaning basin feature
  X['basin'] = X['basin'].str.replace(' ','')
  X['basin'] = X['basin'].str.replace(' ','_')
  X['basin'] = X['basin'].str.replace(',','_')
  X['basin'] = X['basin'].str.replace('_/_','_')
  X['basin'] = X['basin'] .str.lower()

  #cleaning region feature
  X['region'] = X['region'] .str.replace(' ','_')
  X['region'] = X['region'] .str.lower()

  #cleaning lga feature
  X['lga'] = X['lga'] .str.replace(' ','_')
  X['lga'] = X['lga'] .str.lower()

  #cleaning scheme_name feature
  X['scheme_name'] = X['scheme_name'] .str.replace(' ','_')
  X['scheme_name'] = X['scheme_name'] .str.lower()

  #cleaning extraction_type_class feature
  X['extraction_type_class'] = X['extraction_type_class'] .str.replace(' ','_')
  X['extraction_type_class'] = X['extraction_type_class'] .str.replace('-','_')

  #cleaning management feature
  X['management'] = X['management'] .str.replace(' ','_')
  X['management'] = X['management'] .str.replace('-','')
  X['management'] = X['management'] .str.replace('__','')

  #cleaning payment feature
  X['payment'] = X['payment'] .str.replace(' ','_')

  #cleaning source feature
  X['source'] = X['source'] .str.replace(' ','_')

  #cleaning waterpoint_type feature
  X['waterpoint_type'] = X['waterpoint_type'] .str.replace(' ','_')

  return X

def final_fun_1(X):
  #adding operating years of pump
  X['date_recorded'] = pd.to_datetime(X['date_recorded'])
  X['operational_year'] = X.date_recorded.dt.year - X.construction_year

  #replace zero values with np.nan
  X['amount_tsh']=X['amount_tsh'].replace(0,np.nan)
  X['population']=X['population'].replace(0,np.nan)
  X['gps_height']=X['gps_height'].replace(0,np.nan)
  
  #Eliminate features
  features_tobe_eliminated=['construction_year','date_recorded','num_private','water_quality','payment_type','quantity_group','waterpoint_type_group','extraction_type_group','source_type','management_group','district_code','num_private','scheme_management','id','subvillage','wpt_name','recorded_by','permit','public_meeting','ward','extraction_type']
  X1=X.drop(columns=features_tobe_eliminated)

  #Region based median imputation of latitude and longtitude features
  long_medians_test = X1.groupby(['region'])['longitude'].transform('median')
  lat_medians_test = X1.groupby(['region'])['latitude'].transform('median')
  X1['latitude']=X1['latitude'].fillna(lat_medians_test)
  X1['longitude']=X1['longitude'].fillna(long_medians_test)

  #Filling missing values with other
  X1['installer']=X1['installer'].fillna('other')
  X1['funder']=X1['funder'].fillna('other')
  X1['scheme_name']=X1['scheme_name'].fillna('other')

  #function created for cleaning data
  X1=data_cleaning(X1)

  #Mice Imputation
  X_mice = X1.filter(['amount_tsh','gps_height','population'], axis=1).copy()
  mice_imputer = pickle.load(open('mice_imputer.pkl', 'rb'))
  X_mice_imputed = pd.DataFrame(mice_imputer.fit_transform(X_mice), columns=X_mice.columns)
  X1['amount_tsh']=X_mice_imputed['amount_tsh'].values
  X1['gps_height']=X_mice_imputed['gps_height'].values
  X1['population']=X_mice_imputed['population'].values

  #Target Encoding
  enc = pickle.load(open('enc.pkl', 'rb'))
  X_cat=X1.drop(columns=['amount_tsh','population','gps_height','longitude','latitude','operational_year'])
  X_numerical=X1[['amount_tsh','population','gps_height','longitude','latitude','operational_year']]
  X_target_cat=enc.transform(X_cat)
  X_target_cat = X_target_cat.astype(np.float32)
  X_numerical = X_numerical.astype(np.float32)
  test_data=pd.concat([X_target_cat,X_numerical],axis=1)

  #Adding auto_encoder features
  encoder = tf.keras.models.load_model('mice_encoder.h5')
  X_encoded = encoder.predict(test_data)
  X_final = np.hstack((np.array(test_data),X_encoded))

  #predict with best model
  best_model = pickle.load(open('best_model.pkl','rb'))
  y_pred = best_model.predict(X_final)

  y_prediction=[]

  for i in y_pred:
    if i==0.0:
      y_prediction.append("functional - the waterpoint is operational and there are no repairs needed")
    elif i==1.0:
      y_prediction.append("functional needs repair - the waterpoint is operational, but needs repairs")
    else:
      y_prediction.append("non functional - the waterpoint is not operational")

  return y_prediction


if predict_button:
    if data is not None:
        df = pd.read_csv(data)
        st.text('Uploaded Data :')
        st.dataframe(df)
        start = time.time()
        y_pred = final_fun_1(df)
        datapoints = np.arange(1,len(y_pred)+1)
        df_pred = pd.DataFrame()
        df_pred['Datapoint'] = datapoints
        df_pred['Prediction'] = y_pred
        st.text('Predictions :')
        st.dataframe(df_pred)
        end = time.time()
        st.write('Time taken for prediction :', str(round(end-start,3))+' seconds')
    else:
        st.text('Please upload Data')
        
elif test_data:
    test_file = pd.read_csv('sample_data.csv')
    sample = test_file.sample(n=10)
    sample.reset_index(inplace=True,drop=True)
    st.text('Sample Data :')
    st.dataframe(sample)
    start = time.time()
    y_pred = final_fun_1(sample)
    datapoints = np.arange(1,len(y_pred)+1)
    df_pred = pd.DataFrame()
    df_pred['Datapoint'] = datapoints
    df_pred['Prediction'] = y_pred
    st.text('Predictions :')
    st.dataframe(df_pred)
    end = time.time()
    st.write('Time taken for prediction :', str(round(end-start,3))+' seconds')
