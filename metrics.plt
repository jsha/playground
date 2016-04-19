set yrange [0:60]
set ylabel "Percentage of pageloads over HTTPS"
set xdata time
set timefmt "%Y%m%d"
set terminal pngcairo size 1000,700 enhanced font "Helvetica,14"
set output 'pageload_is_ssl.png'
plot \
  "pageload_is_ssl.csv" using 1:3 title "30-day centered moving average" with lines lt rgb "black", \
  "pageload_is_ssl.csv" using 1:2 title "daily" with points pt 7 pointsize 0.3 lc rgb "#BBBBBB"
