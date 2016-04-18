set yrange [36:45]
set ylabel "PAGELOAD IS SSL percentage, 30-day moving average"
set multiplot
set xdata time
set timefmt "%Y%m%d"
plot "pageload_is_ssl.csv" using 1:2 with points pointsize 0
plot "pageload_is_ssl.csv" using 1:3 with lines lt rgb "black"
