# Python 3 Required. Tested in rh-python36 #
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import traceback
import time
import datetime
import multiprocessing 
from matplotlib.dates import DateFormatter
from tcp_latency import measure_latency

# IP List for Reference 
# 113.108.173.31 --- China Telecom Guangzhou (www.gz.gov.cn)
# 117.184.226.77 --- China Mobile Shanghai (www.shanghai.gov.cn)
# 124.93.228.74 --- China Unicom Dalian (www.dl.gov.cn)
# 120.197.33.3 --- China Mobile Guangdong (www.gd.gov.cn)
# 157.122.49.3 --- China Unicom Guangdong (www.gd.gov.cn)

# Specify the test IP/Domains || 测试IP/域名列表
# Specify the data storage file's name || 数据存储文件名列表
# Specify the test port || 测试端口列表
test_host_list = ['113.108.173.31','117.184.226.77', '124.93.228.74']
file_name_list = ['Ch-Telecom Guangzhou.txt', 'Ch-Mobile Shanghai.txt', \
	'Ch-Unicom Dalian.txt']
port_list = [80,80,80]

# Specify the period of the plot (Unit: second) || 指定绘制时间范围（秒）
# Specify the interval between generating the plot (Unit: second) || 指定生成图像间隔（秒）
plot_timespan_list = [6*3600,3*86400,7*86400,15*86400,30*86400]
generating_interval = 60*5

# Data point number (Can be any large #) || 数据采集次数
# Wait time between each TCP connection (Unit: second) || 发起新TCP连接间隔（秒）
number_of_data_points = 365*8640
wait_time_for_each_connection = 10

# Modify the figures (Latency upper limit in plot & DPI) || 调整图像（延迟上限及DPI）
latency_plot_limit = 400
img_dpi = 300

# To avoid pandas warning message || 避免pandas警告信息
pd.plotting.register_matplotlib_converters()

def LatencyDataCollection(t_host_list, t_port_list, t_timeout, t_wait, t_file_name_list):
	# Create a loop for data collection. 
	for i in range(number_of_data_points):
		for ii in range(len(t_host_list)):
			latency_ms = measure_latency(host=t_host_list[ii], port=t_port_list[ii], \
				timeout=t_timeout, runs=1) # latency_ms is a list with one element.
			if latency_ms[0] is None:
				latency_ms = [0]           # If timeout, use 0 to replace the None value.
			time_at_measurement = datetime.datetime.now()
			latency_value = latency_ms[0] 
			
			with open(t_file_name_list[ii], 'a') as data_file:
				data_file.write('%s' % time_at_measurement + ',' + \
					'%s' % latency_value + '\n')
			
		time.sleep(t_wait)             # Wait for next TCP connection.
	return

def PlotGraph(import_file_list, p_frequency, p_timespan_list, p_wait):
	jj = round(2*number_of_data_points*p_wait/p_frequency)
	# Create a loop to update the plot. 
	for j in range(jj):
		time.sleep(p_frequency)        # Wait for generating next plot.
		for p in range(len(p_timespan_list)):
			
			fig, ax = plt.subplots()
			plt.xlabel('Server Time in mm-dd-HH-MM')  
			plt.ylabel('Latency in ms')
			plt.title('TCP Latency Stat Last %s Seconds' % p_timespan_list[p])
			plt.ylim([0,latency_plot_limit])
			myFmt = DateFormatter('%m-%d, %H:%M')    # Set date-time format for x-axis. 
			
			# Plot from each data file. 
			for import_file in import_file_list:
				x_raw, y_raw = np.loadtxt(import_file, \
					dtype='str', delimiter=',', unpack=True)
					
				# It's not the precise # of data points corresponds to that time duration, 
				# since the time consumed in TCP connection is ignored.
				# It does not have significant impact on the plot.
				number_of_lines_selected = round(p_timespan_list[p]/p_wait)
				
				x_raw_selected = x_raw[-number_of_lines_selected:]
				y_raw_selected = y_raw[-number_of_lines_selected:]
				
				x_time = pd.to_datetime(x_raw_selected)        # Convert to datetime type.  
				y_latency = list(map(float, y_raw_selected))   # Convert to float type. 
				
				loss_packet_number = y_latency.count(0)
				loss_packet_rate = round((100*loss_packet_number/len(y_latency)),2)
				average_latency = round((sum(y_latency)/(len(y_latency)- \
					loss_packet_number)),2)
				location_name = import_file[:-4]    # Eliminate '.txt' at the end of filename.
				
				ax.plot(x_time, y_latency, \
					label='ISP: %s||Average Latency: %sms||Loss Packet Rate: %s%%' %\
						(location_name, average_latency, \
							loss_packet_rate), linewidth=0.25, alpha = 0.7) # Use %% to display %
				ax.legend(loc=2)                    # Put the legend at the upper left location.
				ax.xaxis.set_major_formatter(myFmt)
				plt.gcf().autofmt_xdate()	        # Rotate the xlabel text. 
				
			plt.savefig('stat-%s.png' % p_timespan_list[p], bbox_inches='tight', dpi=img_dpi)		
			
			## Uncomment the following lines if you want to keep all historical plots. 
			#current_time = datetime.datetime.now()
			#current_time_str = current_time.strftime('%Y-%m-%d-%H-%M-%S')
			#plt.savefig('stat-%s-%s.png' % (p_timespan_list[p], current_time_str), \
				#bbox_inches='tight', dpi=img_dpi)
			plt.close(fig)

	return
	
### Main Function -------------------------------------------------------------- ###
if __name__ == '__main__':   # Routine Command 

	fcn_latency_argument = [(test_host_list, port_list, 2.5, \
		wait_time_for_each_connection, file_name_list)]
		
	fcn_plot_argument = [(file_name_list, generating_interval, \
		plot_timespan_list, wait_time_for_each_connection)]
		
	# Create a Pool to run data collection and plotting process simultaneously.
	# .starmap method has been adopted to load multiple arguments to one function.
	# _async must be applied since there are two different functions run together.	
	pool_c = multiprocessing.Pool(2)
	pool_c.starmap_async(LatencyDataCollection, fcn_latency_argument)
	pool_c.starmap_async(PlotGraph, fcn_plot_argument)
	
	# Use try-except method to enable Ctrl-C interrupt. 
	# (Multiprocessing Pool will not stop when apply keyboard interrupt directly.)
	try:
		print('Running......')
		# Keep the program in the "try" stage. The Pool will continue to run. 
		for i in range(2*wait_time_for_each_connection*number_of_data_points):
			time.sleep(1) 
		
	except KeyboardInterrupt:
		print("Caught KeyboardInterrupt, terminating workers")
		pool_c.terminate()
		pool_c.join()
		print("Done")
	else:
		print("Quitting normally")
		pool_c.close()
		pool_c.join()
		