python --version

if [ "$1" == "" ]; then
    BASE_URL="https://www.nextprot.org"
else
    BASE_URL=$1
fi
echo "BASE_URL: $BASE_URL"

if [ "$3" == "" ]; then
    echo "2nd argument not set, therefore using all files (specs) !!!!!!!!! "
    python check.py --baseUrl $BASE_URL
else
    echo "Using test file $3"
    python check.py --baseUrl $BASE_URL --file $3
fi

# Check multiple times in case pre-rendering tool crashes in a test
RETRY=$2
while [ $RETRY -lt 10 ] && [ -f errors.tsv ]; do
  if [ -f errors.tsv ]
  then
      echo "\n\nRetrying with the remaining errors in 3 seconds ... "
      sleep 3
      python check.py --baseUrl $BASE_URL --file errors.tsv
  else
      rm errors.tsv
      echo "Success ! No more errors!"
  fi
  let RETRY=RETRY+1 
done
         

# Check if there are still some errors
if [ -f errors.tsv ]; then
   read lines words chars filename <<< $(wc errors.tsv)
   #need to remove the header
   errorsCount=`expr $lines - 1`
   printf "Failed with $errorsCount errors:\n"
   cat errors.tsv
   exit 1
else
  echo "Finished successfully!"
fi
