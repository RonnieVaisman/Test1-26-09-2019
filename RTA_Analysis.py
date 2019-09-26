import os
import sys
import datetime
import time
import re
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.pyplot import figure
from matplotlib.widgets import MultiCursor
# We will use the Seaborn library
import seaborn as sns
sns.set()

def Handle_RTA_Input():
     global MinCapacityFile_FromROAD, RSSFile_FromROAD,  Site_Name, UL_Ration, UL_DL_Ration_Anomaly_Threshould, Min_Num_BS_to_pass, \
     Do_BuildMax_RSS_Graph, Num_ALPMs_To_Prosses, Do_Present_Overall_ALPM_Charts

     RTA_Input_Params = pd.read_csv('RTA_Input.csv')
     MinCapacityFile_FromROAD = RTA_Input_Params.loc[0,'MinCapacity File Name']
     RSSFile_FromROAD = RTA_Input_Params.loc[0,'RSS File Name']
     Site_Name = RTA_Input_Params.loc[0,'Site Name (Optional)']
     UL_Ration = RTA_Input_Params.loc[0,'UL Ration']
     UL_DL_Ration_Anomaly_Threshould = RTA_Input_Params.loc[0,'UL_DL_Ration_Anomaly Threshould']
     Min_Num_BS_to_pass             = RTA_Input_Params.loc [0,'Min Number of BS to pass']
     Do_BuildMax_RSS_Graph          = RTA_Input_Params.loc [0,'Do_BuildMax_RSS_Graph(For BS and MU)']
     Num_ALPMs_To_Prosses           = RTA_Input_Params.loc [0,'Number Of ALPM files to Analize']
     Do_Present_Overall_ALPM_Charts = RTA_Input_Params.loc [0,'Do_Present_Overall_ALPM_Charts']
     return

def PrepareOutputDir():
     now = datetime.datetime.now()
     CurrentTime = now.strftime("_Date_%d-%m-%Y_Time_%H-%M-%S")
     Output_DirName = 'RTA_Results_' + Site_Name + CurrentTime
     os.mkdir(Output_DirName)
     return Output_DirName

def Discover_ROAD_Input(FileName):
     global UL_Tresh, DL_Tresh, Min_Interval_Time_Threh
     maketrainsim_input_string = pd.read_csv(FileName, sep =' ', nrows = 0)
     UL_Tresh = round(float(maketrainsim_input_string.columns[9]))
     DL_Tresh = round(float(maketrainsim_input_string.columns[12]))
     Min_Interval_Time_Threh = int(maketrainsim_input_string.columns[15])
     print("UL Threshould (Mbps) = {0};  DL Threshould (Mbps) = {1}; Minimum Interval (sec) = {2}".format( UL_Tresh, DL_Tresh, Min_Interval_Time_Threh))

     DL_Ration = 100 - UL_Ration
     UL_DL_Ration = UL_Ration/DL_Ration
     print ("UL_Ration/DL_Ration = {0}".format(UL_DL_Ration))
     return 

def BadSec_BS_MU_ALPM(RSSFile, LowCapPerAlpm, NumDB2Proccess, PassedBSsTrh, Output_DirName):
     global UL_Tresh, DL_Tresh, Min_Interval_Time_Threh
     #Part 1: To discover MU that visited more than PassedBSsTrh BSs shall Proccess RSS Table 
     #Create array of dataframes that includes only relevant MUs. DataFrame per alpm.db
     RSS_Tbl = pd.read_csv(RSSFile)
     #remove last column with Statistic of Median RSS per MU
     RSS_Tbl.drop(RSS_Tbl.columns[len(RSS_Tbl.columns)-1], axis=1, inplace=True)
     i,j, k = 0,0,0
     df_db = {}
     #Special case handle in RSS file proccessin (first row is interpreted by pandas as columns)
     df_db[i] = pd.DataFrame(columns = RSS_Tbl.columns)
     Current_alpm_file_name = RSS_Tbl.columns[0]
     print('Analysing alpm file for RSS: ' +  Current_alpm_file_name)
     for index, row in RSS_Tbl.iterrows():
          #print ('row ' + str(row))
          if (".db" in str(row[0])):
               Current_alpm_file_name = row[0]
               print('Analysing alpm file for RSS: ' +  Current_alpm_file_name)
               df_db[i] = pd.DataFrame(columns = RSS_Tbl.columns)
          if ("Median of HMUs per Bases" in str(row[0])):
               #Got Only MU that passed >= PassedBSsTrh
               df_db[i] = df_db[i][df_db[i].notnull().sum(axis=1)>PassedBSsTrh]
               #replace RSS values to default Bad Sec value = 0
               df_db[i].replace(regex='\'.*\'', value=1, inplace=True)
               df_db[i].rename(columns = {df_db[i].columns[0]:Current_alpm_file_name}, inplace = True)
               df_db[i].fillna(value=-1, inplace=True)
               #FOR DEBUG, DO NOT REMOVE!!!
               #df_db[i].to_csv(Output_DirName + '\\' + "Intermidiate_RssTable_" + str(i) + '.csv')
               if (i == NumDB2Proccess - 1):
                    break
               i = i + 1
               j = 0
          else:
               df_db[i].loc[j] = RSS_Tbl.iloc[k] #append new row
               j = j + 1
          if ("HMUS median per Base for All Files" in str(row[0])):
               break
          k = k+1

     #Part2: Create array of MinCap dataframes. DataFrame per alpm.db
     df = LowCapPerAlpm
     i,j, k = 0,0,0
     df_db_MinCap = {}
     for index, row in df.iterrows():
          if ((k == 0) & (".db" in str(row[0]))):
               df_db_MinCap[i] = pd.DataFrame(columns = df.columns)  
               Current_alpm_file_name = row[0]
               print('Analysing alpm file for Low Capacity: ' +  Current_alpm_file_name)
          else:
               if (".db" in str(row[0])):
                    Current_alpm_file_name = row[0]
                    #FOR DEBUG, DO NOT REMOVE!!!  
                    #df_db_MinCap[i].to_csv(Output_DirName + '\\' + "Intermidiate_Low Capacity" + str(i) + '.csv')
                    i = i + 1
                    df_db_MinCap[i] = pd.DataFrame(columns = df.columns)
                    if (i == NumDB2Proccess):
                         break
                    print('Analysing alpm file for Low Capacity: ' +  Current_alpm_file_name)
                    j = 0
               else:
                    df_db_MinCap[i].loc[j] = df.iloc[k]
                    j = j + 1
          k = k+1
     #Part3: For each alpm file (represented by pair of : )
     BadSec_DF = {}
     for n in range(0, NumDB2Proccess): #Loop over alpm Files
          BadSec_DF[n] = df_db[n]
          for index, row in df_db[n].iterrows(): #Loop over  MUs that visited more than Thr BSs 
               CurrentMU = row[0]
               for index1, row1 in df_db_MinCap[n].iterrows():
                    if (df_db_MinCap[n].loc[index1,'HMUIP'] == CurrentMU): #Loop and summurize over all cases where specific MU have low capacity
                         BadSec_DF[n].loc[index, df_db_MinCap[n].loc[index1,'ConBase']] = BadSec_DF[n].loc[index, df_db_MinCap[n].loc[index1,'ConBase']] + df_db_MinCap[n].loc[index1,'intervalSec']
          #FOR DEBUG, DO NOT REMOVE!!! 
          #BadSec_DF[n].to_csv(Output_DirName + '\\' + "Intermidiate_BadSec" + str(n) + '.csv')
          Current_alpm_file_name = BadSec_DF[n].columns[0]
          print('Build Aggregated Bad Sec graps from file: ' +  Current_alpm_file_name)
          YY= BadSec_DF[n].set_index(BadSec_DF[n].columns[0])
          #remove from BS IP all digits before last "."
          for l in range(0, len(BadSec_DF[n].columns)-1):
               YY.rename(columns = {YY.columns[l]:re.sub(r'.*\..*\..*\.','',YY.columns[l])}, inplace = True)
          ZZ=YY.transpose()
          if (BadSec_DF[n].shape[0]>0):
               ax = ZZ.plot(kind='bar', stacked=True, figsize=(13,10), title="Sum. of ALL Bad seconds cases for UL&DL x MU (passed > 5 BS) x BS (all BSs in Line), Params: UL Thr (Mbps) = {0};  DL Thr (Mbps) = {1}; Minimum Interval (sec) = {2}".format( UL_Tresh, DL_Tresh, Min_Interval_Time_Threh) )
               ax.axhline(y=0, color='black', linestyle='-')
               ax.set_xlabel('BS IP addresses')
               ax.set_ylabel('Bad seconds')
               ax.autoscale(enable = True, axis = 'y', tight = True)
               plt.savefig(Output_DirName + '\\' + 'BadSecondsStackedBar' + Current_alpm_file_name + '.jpg')
          else:
               print("No trains that passes 5 BSs in the file " + Current_alpm_file_name)
     plt.show()

def Visualize_BS_MedianOfMaxRSS(RSSFile_FromROAD, Output_DirName):
     global Site_Name
     RSS_Tbl = pd.read_csv(RSSFile_FromROAD)
     #print(RSS_Tbl.head(1))

     #Find line with Overall_MedianRSS_PerBS
     Overall_MedianRSS_PerBS = RSS_Tbl[RSS_Tbl.iloc[:,0].str.contains("HMUS median per Base for All Files")==True]
     #Drop first and last column
     Overall_MedianRSS_PerBS.drop(Overall_MedianRSS_PerBS.columns[0], axis=1, inplace=True)
     Overall_MedianRSS_PerBS.drop(Overall_MedianRSS_PerBS.columns[len(Overall_MedianRSS_PerBS.columns)-1], axis=1, inplace=True)
     #remove "\"
     Overall_MedianRSS_PerBS.replace(regex='\'', value='', inplace=True)
     #Calc number of streams
     NumberOfStreams = str(Overall_MedianRSS_PerBS.iloc[0,1]).count('-') 

     #remove from BS IP address first 3 nibles.  It permit drow x label of graph more compact.
     for l in range(0, len(Overall_MedianRSS_PerBS.columns)):
          Overall_MedianRSS_PerBS.rename(columns = {Overall_MedianRSS_PerBS.columns[l]:re.sub(r'.*\..*\..*\.','',Overall_MedianRSS_PerBS.columns[l])}, inplace = True)
     
     #Option A:
     #replace empty cells, It make distortion to scale & Median
     #    Overall_MedianRSS_PerBS = Overall_MedianRSS_PerBS.fillna('-60/-60/-60')
     #Option B:
     #remove remove non visited BSs
     xxx = Overall_MedianRSS_PerBS.dropna(axis=1, how='any', thresh=None, subset=None) #remove empty columns
     Overall_MedianRSS_PerBS = xxx

     #print(Overall_MedianRSS_PerBS.head(1))
     #print(NumberOfStreams)
     #Create different dataframe per chain
     with open(Output_DirName + '\\' + 'ProccessedRSSTbleBS'  + '.csv', mode='w') as ProccessedRSS_File:
          Overall_MedianRSS_PerBS_Ch1 = Overall_MedianRSS_PerBS.replace(regex='\/.*', value='').astype('int')
          Overall_MedianRSS_PerBS_Ch1.to_csv(ProccessedRSS_File, header=True, line_terminator='\n')

          Overall_MedianRSS_PerBS_Ch2 = Overall_MedianRSS_PerBS.replace(regex='^-[0-9][0-9]\/|^-[0-9][0-9][0-9]\/', value='')
          Overall_MedianRSS_PerBS_Ch2 = Overall_MedianRSS_PerBS_Ch2.replace(regex='\/.*', value='').astype('int')
          Overall_MedianRSS_PerBS_Ch2.to_csv(ProccessedRSS_File, header=False, line_terminator='\n')

          if (NumberOfStreams == 3):
               Overall_MedianRSS_PerBS_Ch3 = Overall_MedianRSS_PerBS.replace(regex='.*\/', value='').astype('int')
               Overall_MedianRSS_PerBS_Ch3.to_csv(ProccessedRSS_File, header=False, line_terminator='\n')

          #Plot in one chart ALL Chains
          plt.figure(figsize=(20, 10))
          plt.suptitle(Site_Name + ' BS Median of Max RSS over all passed MUs ')
          plt.plot(Overall_MedianRSS_PerBS_Ch1.columns, Overall_MedianRSS_PerBS_Ch1.iloc[0,:], marker='o', color='r', label='Ch1')
          plt.plot(Overall_MedianRSS_PerBS_Ch2.columns, Overall_MedianRSS_PerBS_Ch2.iloc[0,:], marker='o', color='b', label='Ch2')
          plt.xticks(rotation='vertical') #Need for site with big num of BS (like WH7)
          if (NumberOfStreams == 3):
               plt.plot(Overall_MedianRSS_PerBS_Ch3.columns, Overall_MedianRSS_PerBS_Ch3.iloc[0,:], marker='o', color='g', label='Ch3')
          plt.legend(loc='upper right')
          plt.savefig(Output_DirName + '\\' + 'MedianMaxRSSperBS1' + '.jpg')
          

          #Plot in chart per chain
          plt.figure(figsize=(20, 10))
          plt.suptitle(Site_Name + ' BS Median of Max RSS over all passed MUs ')

          plt.subplot(3,1,1)
          plt.plot(Overall_MedianRSS_PerBS_Ch1.columns, Overall_MedianRSS_PerBS_Ch1.iloc[0,:], marker='o', color='r', label='Ch1')
          plt.axhline(y=Overall_MedianRSS_PerBS_Ch1.iloc[0,:].median(), color='r', linestyle=':', label='Median')
          plt.xticks(rotation='vertical') #Need for site with big num of BS (like WH7)
          plt.legend(loc='upper right')
          
          plt.subplot(3,1,2)
          plt.plot(Overall_MedianRSS_PerBS_Ch2.columns, Overall_MedianRSS_PerBS_Ch2.iloc[0,:], marker='o', color='b', label='Ch2')
          plt.axhline(y=Overall_MedianRSS_PerBS_Ch2.iloc[0,:].median(), color='b', linestyle=':', label='Median')
          plt.xticks(rotation='vertical') #Need for site with big num of BS (like WH7)
          plt.legend(loc='upper right')
          if (NumberOfStreams == 3):
               plt.subplot(3,1,3)
               plt.plot(Overall_MedianRSS_PerBS_Ch3.columns, Overall_MedianRSS_PerBS_Ch3.iloc[0,:], marker='o', color='g', label='Ch3')
               plt.axhline(y=Overall_MedianRSS_PerBS_Ch3.iloc[0,:].median(), color='g', linestyle=':', label='Median')
               plt.xticks(rotation='vertical') #Need for site with big num of BS (like WH7)
               plt.legend(loc='upper right')
          plt.savefig(Output_DirName + '\\' + 'MedianMaxRSSperBS2' + '.jpg')

          plt.show()
     ProccessedRSS_File.close()
     return

def Visualize_MU_MedianOfMaxRSS(RSSFile_FromROAD, Output_DirName):
     global Site_Name
     RSS_Tbl = pd.read_csv(RSSFile_FromROAD)
     #print(RSS_Tbl.head(1))
     RSS_Tbl.set_index(RSS_Tbl.columns[0], inplace=True) # set column 0 of RSS_Tble to be index
     row_index = RSS_Tbl.index.get_loc('HMU Median for all Files') #find row where MU median RSS is
     print('rox_index =',row_index )
     MU_MedianOfMax_DF = RSS_Tbl.iloc[row_index:RSS_Tbl.shape[0], 0:1] #get apropriate subdataframe
     MU_MedianOfMax_DF.dropna(axis=0, how='any', thresh=None, subset=None, inplace=True) #remove empty strings

     MU_MedianOfMax_DF.replace(regex='\'', value='', inplace=True) #remove " '  "
     NumberOfStreams = str(MU_MedianOfMax_DF.iloc[0,0]).count('-') #Calc number of streams
     MU_MedianOfMax_DF_T = MU_MedianOfMax_DF.transpose()

     #Create different dataframe per chain
     with open(Output_DirName + '\\' + 'ProccessedRSSTbleMU'  + '.csv', mode='w') as ProccessedRSS_File:
          Overall_MedianRSS_PerMU_Ch1 = MU_MedianOfMax_DF_T.replace(regex='\/.*', value='').astype('int')
          Overall_MedianRSS_PerMU_Ch1.to_csv(ProccessedRSS_File, header=True, line_terminator='\n')
          print(Overall_MedianRSS_PerMU_Ch1.head(5))

          Overall_MedianRSS_PerMU_Ch2 = MU_MedianOfMax_DF_T.replace(regex='^-[0-9][0-9]\/|^-[0-9][0-9][0-9]\/', value='')
          Overall_MedianRSS_PerMU_Ch2 = Overall_MedianRSS_PerMU_Ch2.replace(regex='\/.*', value='').astype('int')
          Overall_MedianRSS_PerMU_Ch2.to_csv(ProccessedRSS_File, header=False, line_terminator='\n')

          if (NumberOfStreams == 3):
               Overall_MedianRSS_PerMU_Ch3 = MU_MedianOfMax_DF_T.replace(regex='.*\/', value='').astype('int')
               Overall_MedianRSS_PerMU_Ch3.to_csv(ProccessedRSS_File, header=False, line_terminator='\n')

          plt.figure(figsize=(20, 10))
          plt.suptitle(Site_Name + ' MU Median of Max RSS over all passed BSs ')
          plt.plot(Overall_MedianRSS_PerMU_Ch1.columns, Overall_MedianRSS_PerMU_Ch1.iloc[0,:], marker='o', color='r', label='Ch1')
          plt.plot(Overall_MedianRSS_PerMU_Ch2.columns, Overall_MedianRSS_PerMU_Ch2.iloc[0,:], marker='o', color='b', label='Ch2')
          if (NumberOfStreams == 3):
               plt.plot(Overall_MedianRSS_PerMU_Ch3.columns, Overall_MedianRSS_PerMU_Ch3.iloc[0,:], marker='o', color='g', label='Ch3')
          plt.legend(loc='upper right')
          plt.savefig(Output_DirName + '\\' + 'MedianMaxRSSperMU_1' + '.jpg')
          
          
          plt.figure(figsize=(20, 10))
          plt.suptitle(Site_Name + ' MU Median of Max RSS over all passed BSs ')
          plt.subplot(3,1,1)
          plt.plot(Overall_MedianRSS_PerMU_Ch1.columns, Overall_MedianRSS_PerMU_Ch1.iloc[0,:], marker='o', color='r', label='Ch1')
          plt.axhline(y=Overall_MedianRSS_PerMU_Ch1.iloc[0,:].median(), color='r', linestyle=':', label='Median')
          plt.legend(loc='upper right')
          plt.subplot(3,1,2)
          plt.plot(Overall_MedianRSS_PerMU_Ch2.columns, Overall_MedianRSS_PerMU_Ch2.iloc[0,:], marker='o', color='b', label='Ch2')
          plt.axhline(y=Overall_MedianRSS_PerMU_Ch2.iloc[0,:].median(), color='b', linestyle=':', label='Median')
          plt.legend(loc='upper right')
          if (NumberOfStreams == 3):
               plt.subplot(3,1,3)
               plt.plot(Overall_MedianRSS_PerMU_Ch3.columns, Overall_MedianRSS_PerMU_Ch3.iloc[0,:], marker='o', color='g', label='Ch3')
               plt.axhline(y=Overall_MedianRSS_PerMU_Ch3.iloc[0,:].median(), color='g', linestyle=':', label='Median')
          plt.legend(loc='upper right')
          plt.savefig(Output_DirName + '\\' + 'MedianMaxRSSperMU_2' + '.jpg')
          plt.show()
     ProccessedRSS_File.close()
     return

def PrepareLowCapacityFiltered_DF_and_File():
     MinCapacityTable = pd.read_csv(MinCapacityFile_FromROAD, skiprows=3)
     MinCapacityTable = MinCapacityTable[(MinCapacityTable.PotAvg != 0) & (MinCapacityTable.InversePotAvg != 0)]
     print ("Filtered MinCapacityTable's shape: = {0}".format(MinCapacityTable.shape))

     MinCapacityPerALPM_DF = MinCapacityTable[((MinCapacityTable.Direction == 'UL') & (MinCapacityTable.PotAvg < UL_Tresh)) |  ((MinCapacityTable.Direction == 'DL') & (MinCapacityTable.PotAvg < DL_Tresh)) |  (MinCapacityTable.HMUIP.isnull()==True)]

     MinCapacityTable.dropna(subset=['HMUIP'], inplace=True)
     # Create DF with relevant to potential capacity ONLY. ( columns relevant to actual capacity are filtered out
     PotCapTbl = MinCapacityTable.iloc[:, np.r_[0:8 , 20:27 ,29:36, 38, 39, 41 ]]
     #print(PotCapTbl.head (3))

     PotCapTbl1 = PotCapTbl.replace(regex='in Station.*\\:', value='')
     PotCapTbl1['inStation'].fillna(0, inplace = True)

     #Insert column UL ration, Evaluate it  values.
     PotCapTbl1.insert(8, "Eval_UL_Ration (%)", "", True)
     PotCapTbl1.insert(9, "Anomal UL_DL ration", "", True)

     for index, row in PotCapTbl1.iterrows():
          if (row.Direction == 'UL'):
               PotCapTbl1.loc[index, 'Eval_UL_Ration (%)'] = round (row.PotAvg*100/(row.PotAvg + row.InversePotAvg))
          else:
               PotCapTbl1.loc[index, 'Eval_UL_Ration (%)'] = round (row.InversePotAvg*100/(row.PotAvg + row.InversePotAvg))

          if (PotCapTbl1.loc[index, 'Eval_UL_Ration (%)'] - UL_Ration > UL_DL_Ration_Anomaly_Threshould):
               PotCapTbl1.loc[index, 'Anomal UL_DL ration'] = "Bad DL"
          else:
               if (UL_Ration - PotCapTbl1.loc[index, 'Eval_UL_Ration (%)'] > UL_DL_Ration_Anomaly_Threshould):
                    PotCapTbl1.loc[index, 'Anomal UL_DL ration'] = "Bad UL "
               else:
                    PotCapTbl1.loc[index, 'Anomal UL_DL ration'] = "UL/DL Ok"

     # Copy to Low_PotentialCapacity_ file the intervals where all samples < X or average for interval < X
     LowCapacityTbl = PotCapTbl1[((PotCapTbl1.Direction == 'UL') & (PotCapTbl1.PotAvg < UL_Tresh)) |  ((PotCapTbl1.Direction == 'DL') & (PotCapTbl1.PotAvg < DL_Tresh))]
     LowCapacityTbl.to_csv (Output_DirName + '\\' + 'Low_PotentialCapacity_'  + '.csv')  
     return (LowCapacityTbl, MinCapacityPerALPM_DF)

def Write_OverallALPMs_AnalyticsTablesToFile():
     with open(Output_DirName + '\\' + 'Analysis_'  + '.csv', mode='w') as Analysis_File:
          Analysis_File.write("************************Bad seconds (< UL or DL Treshould) vs RSS (H/M/L) distribution**************************************************\n")
          LowCapacityTbl.groupby(['MedianRSSLevel-H/M/L'])['intervalSec'].sum().to_csv(Analysis_File, header=True, line_terminator='\n')

          Analysis_File.write("***********************************Bad seconds (< UL or DL Treshould) vs Direction (DL/UL) distribution***************************************\n")
          LowCapacityTbl.groupby(['Direction'])['intervalSec'].sum().to_csv(Analysis_File, header=True,   line_terminator='\n')

          Analysis_File.write("**************************************Bad seconds (< UL or DL Treshould) vs BS distribution************************************\n")
          LowCapacityTbl.groupby(['ConBase'])['intervalSec'].sum().to_csv(Analysis_File, header=True,  line_terminator='\n')

          Analysis_File.write("********************************Bad seconds (< UL or DL Treshould) vs MU distribution******************************************\n")
          LowCapacityTbl.groupby(['HMUIP'])['intervalSec'].sum().to_csv(Analysis_File, header=True,  line_terminator='\n')

          Analysis_File.write("****************************Bad seconds (< UL or DL Treshould) vs Same BS/Not same BS distribution**********************************************\n")
          LowCapacityTbl.groupby(['Samebase'])['intervalSec'].sum().to_csv(Analysis_File, header=True,  line_terminator='\n')

          Analysis_File.write("***************************Bad seconds (< UL or DL Treshould) vs Train under BS Yes/No  distribution***********************************************\n")
          LowCapacityTbl.groupby(['Suspected'])['intervalSec'].sum().to_csv(Analysis_File, header=True,  line_terminator='\n')

          Analysis_File.write("***************************Bad seconds when UL/DL ration become ANOMAL  vs BS distribution***********************************************\n")
          LowCapacityTbl.groupby(['Anomal UL_DL ration', 'ConBase'])['intervalSec'].sum().to_csv(Analysis_File, header=True,  line_terminator='\n')
          
          Analysis_File.write("*************************pivot_table Bad second dependancy RSS vs BS *************************************************\n")
          LowCapacityTbl.pivot_table( index=["MedianRSSLevel-H/M/L"], columns=["ConBase"], values=["intervalSec"], aggfunc=np.sum).to_csv(Analysis_File, header=True,  line_terminator='\n')
          
          Analysis_File.write("************************Bad seconds in station analaysis**************************************************\n")
          LowCapacityTbl[(LowCapacityTbl.inStation != 0)].groupby(['ConBase', 'HMUIP', 'Direction', 'MedianRSSLevel-H/M/L'])['intervalSec'].sum().to_csv(Analysis_File, header=True,  line_terminator='\n')
          Analysis_File.write("**************************************************************************\n")

          Analysis_File.write("*************************Count number of intervals when Band seconds strted at IBHO moment with correlation to RSS *************************************************\n")
          LowCapacityTbl[ (LowCapacityTbl.PrevIBHO < 1) & (LowCapacityTbl.PrevIBHO > -1)].groupby(['MedianRSSLevel-H/M/L'])['PrevIBHO'].count().to_csv(Analysis_File, header=True,  line_terminator='\n')

          Analysis_File.close()
     return

def Present_Overall_ALPM_Charts():
     LowCapacityTbl.groupby(['MedianRSSLevel-H/M/L'])['intervalSec'].sum().plot.bar(figsize=(20,20), title='All alpms Bad seconds vs RSSLevel ')
     #plt.gcf().canvas.set_window_title('MedianRSSLevel')
     plt.ylabel('Bad seconds')
     plt.xlabel('RSS level (High, Median, Low)')
     plt.savefig(Output_DirName + '\\' + 'MedianRSSLevel-High Med Low' + '.jpg')
     plt.figure() 


     LowCapacityTbl.groupby(['Direction'])['intervalSec'].sum().plot.bar(figsize=(20,20), title='All alpms Bad seconds RSSLevel vs DL, UL') 
     #plt.gcf().canvas.set_window_title('DL/UL')
     plt.ylabel('Bad seconds')
     plt.xlabel('UL/DL')
     plt.savefig(Output_DirName + '\\' + 'DL or UL' + '.jpg')
     plt.figure()

     LowCapacityTbl.groupby(['ConBase','HMUIP'])['intervalSec'].sum().unstack().plot(kind='bar',stacked=True, figsize=(20,20), title='All alpms bad seconds per BS per MU.')
     #plt.gcf().canvas.set_window_title('BS vs MU')
     plt.ylabel('Bad seconds')
     plt.xlabel('BS IP address (problematic BS only)')
     plt.savefig(Output_DirName + '\\' + 'BS vs MU bad seconds' + '.jpg')
     plt.figure() 

     LowCapacityTbl.groupby(['HMUIP'])['intervalSec'].sum().plot.bar(figsize=(15,15), title='All alpms Bad seconds per MU')
     #plt.gcf().canvas.set_window_title('HMUIP')
     plt.savefig(Output_DirName + '\\' + 'HMUIP' + '.jpg')
     plt.ylabel('Bad seconds')
     plt.xlabel('MU IP address')
     plt.figure() 

     #LowCapacityTbl.groupby(['Samebase'])['intervalSec'].sum().plot.bar(figsize=(20,20), title='All alpms MUs at same BS or diffrent BS')
     #plt.gcf().canvas.set_window_title('Samebase')
     #plt.ylabel('Bad seconds') 
     #plt.savefig(Output_DirName + '\\' + 'Samebase' + '.jpg')
     
     #LowCapacityTbl.groupby(['Suspected'])['intervalSec'].sum().plot.bar()
     #plt.gcf().canvas.set_window_title('Suspected')
     #plt.figure() 

     #LowCapacityTbl[ (LowCapacityTbl.inStation != 0)].groupby(['ConBase', 'HMUIP', 'Direction', 'MedianRSSLevel-H/M/L'])['intervalSec'].sum().plot.bar()
     #plt.gcf().canvas.set_window_title('ConBase, inStation, Direction, MedianRSSLevel-H/M/L')
     #plt.figure() 

     LowCapacityTbl[ (LowCapacityTbl.PrevIBHO < 1) & (LowCapacityTbl.PrevIBHO > -1)].groupby(['MedianRSSLevel-H/M/L'])['MedianRSSLevel-H/M/L'].count().plot.bar(figsize=(20,20), title = 'Number of cases where Low Cap  interval starts @ IBHO Moment, RSS Distribution')
     #plt.gcf().canvas.set_window_title('Counts cases where Low Cap starts @ IBHO Moment, RSS Distribution')
     plt.ylabel('Bad seconds')
     plt.xlabel('RSS Level')
     plt.savefig(Output_DirName + '\\' + 'LowCapacity_at_IBHO Moment_vs_RSS' + '.jpg')
     plt.figure() 

     plt.show()
     return

#Start of Main
print ("RTA Analysis - v1 ")

#Initilize variables
MinCapacityFile_FromROAD, RSSFile_FromROAD, Site_Name,   UL_Ration, UL_DL_Ration_Anomaly_Threshould, Min_Num_BS_to_pass, Num_ALPMs_To_Prosses, Do_BuildMax_RSS_Graph, Do_Present_Overall_ALPM_Charts = \
"empty str",              "empty str",      "empty str", 70,        20,                              5,                  1,                    'No',                  'No'                   

Handle_RTA_Input()

#Proccess Input parameters from first row of MinCapacityxxx.csv generated by maketrainsim
UL_Tresh, DL_Tresh, Min_Interval_Time_Threh = 0,0,0
Discover_ROAD_Input(MinCapacityFile_FromROAD)

Output_DirName = PrepareOutputDir()

LowCapacityTbl, MinCapacityPerALPM_DF  = PrepareLowCapacityFiltered_DF_and_File()

if (Do_BuildMax_RSS_Graph == 'Yes'):
     Visualize_BS_MedianOfMaxRSS(RSSFile_FromROAD, Output_DirName)
     Visualize_MU_MedianOfMaxRSS(RSSFile_FromROAD, Output_DirName)


if (Num_ALPMs_To_Prosses != 0):
     BadSec_BS_MU_ALPM(RSSFile_FromROAD, MinCapacityPerALPM_DF, Num_ALPMs_To_Prosses, Min_Num_BS_to_pass, Output_DirName)

Write_OverallALPMs_AnalyticsTablesToFile()

if (Do_Present_Overall_ALPM_Charts == 'Yes'):
     Present_Overall_ALPM_Charts()


# fig, axes = plt.subplots(3, 1)
# fig.set_size_inches(19, 15)
# fig.suptitle('WS recording ')



# df1.loc[:, "Median Sync RSS"].plot(ax=axes[0], marker='o', color='y')
# axes[0].set_ylabel('Median Sync RSS')
# axes[0].grid()

# df1.loc[:, "Num Valid Sessions"].plot(ax=axes[1], marker='o', color='b')
# axes[1].set_ylabel('Num Valid Sessions')
# axes[1].grid()

# df1.loc[:, "Time Offset"].plot(ax=axes[2], linestyle='--', marker='o', color='g')
# axes[2].set_ylabel('TO (ns)')
# axes[2].grid()
# multi = MultiCursor(fig.canvas, (axes[0], axes[1], axes[2]), color='r', lw=1)


#RSS_Plt = df1.loc[10:50, "Median Sync RSS"].plot(marker='o')
#VS_Plt = df1.loc[10:50, "Num Valid Sessions"].plot( marker='o')
#TO_Plt = df1.loc[10:50, "Time Offset"].plot( linestyle='--', marker='o')

#RSS_Plt = df1.loc[10:50, "Median Sync RSS"].plot(ax=axes[0,0], marker='o' )
#VS_Plt = RSS_Plt.twinx()
#VS_Plt = df1.loc[10:50, "Num Valid Sessions"].plot(marker='o')
#TO_Plt = df1.loc[10:50, "Time Offset"].plot(linestyle='--', marker='o')

#plt.legend(['Median Sync RSS', 'Num Valid Sessions', 'Time Offset'])
#RSS_Plt.set_ylabel('TO (ns)')



# df3 = pd.DataFrame ( { "Median Sync RSS" : df1.loc[:, "Median Sync RSS"],  "Num Valid Sessions" : df1.loc[:, "Num Valid Sessions"], "Time Offset": df1.loc[:,"Time Offset"] })
# print (df3)
# print (df3.corr())

# f = plt.figure(figsize=(19, 15))
# plt.matshow(df3.corr(), fignum=f.number)
# plt.xticks(range(df3.shape[1]), df3.columns, fontsize=14, rotation=45)
# plt.yticks(range(df3.shape[1]), df3.columns, fontsize=14)
# cb = plt.colorbar()
# cb.ax.tick_params(labelsize=14)
# plt.title('Correlation Matrix', fontsize=16)
# plt.show()

# plt.rc('grid', linestyle="-", color='red')
# plt.grid(True) # !!! Look like plt.grid(True) shall be immediatle before plt.show()
# g = input("Press enter") 

#plt.show()





# Calculate covariance for RSS & TO.
# #input("Press Enter to quit ")
#  insteaf of xlwriter use xlwings cause this appends new data to existing file
# a = plt.figure('')
# plt.add_subplot() 
# How to use Pandas the RIGHT way to speed up your code https://towardsdatascience.com/how-to-use-pandas-the-right-way-to-speed-up-your-code-4a19bd89926d
#https://matplotlib.org/3.1.0/gallery/subplots_axes_and_figures/subplots_demo.html
#https://matplotlib.org/1.2.1/examples/pylab_examples/histogram_demo.html
#heat map https://seaborn.pydata.org/generated/seaborn.heatmap.html