#!/bin/bash

BASE_URL=http://localhost:8009
TOKEN=1234567
curl --data "token=$TOKEN&amount=$1&text=$2" $BASE_URL/submit/income/
