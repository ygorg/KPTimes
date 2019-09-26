# (146/313)*260000/60/60
# (1367/2987)*260000/60/60
cat ../*.filelist | cut -f 2 | wget --wait=0.5 --random-wait --no-clobber -nv --force-directories --input-file -
