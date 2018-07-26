python --version

if [ "$1" == "" ]; then
    BASE_URL="https://www.nextprot.org"
else
    BASE_URL=$1
fi
echo "BASE_URL: $BASE_URL"

if [ "$2" == "" ]; then
    echo "2nd argument not set, therefore using all files (specs) !!!!!!!!! "
    python check.py --baseUrl $BASE_URL
else
    echo "Using test file $2"
    python check.py --baseUrl $BASE_URL --file $2
fi

# Check multiple times in case pre-rendering tool crashes in a test
COUNTER=0
while [ $COUNTER -lt 3 ] && [ -f errors.tsv ]; do
  if [ -f errors.tsv ]
  then
      echo "\n\nRetrying with the remaining errors in 3 seconds ... "
      sleep 3
      python check.py --baseUrl $BASE_URL --file errors.tsv
  else
      rm errors.tsv
      echo "Success ! No more errors!"
  fi
  let COUNTER=COUNTER+1 
done
         

# Check if there are still some errors
if [ -f errors.tsv ]; then
   read lines words chars filename <<< $(wc errors.tsv)
   echo "Failed with $lines errors:\n"
   cat errors.tsv
   exit 1
else
  echo "Finished successfully!"
fi
