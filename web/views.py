# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from json import JSONEncoder

import datetime
from django.http import JsonResponse
from django.shortcuts import render

from web.models import *
# Create your views here.
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def submit_income(request):
    """" exspense add """
    # TODO: might be fake

    thisToken = request.POST['token']
    thisUser = User.objects.filter(token__token=thisToken).get()

    if 'date' in request.POST:
        date = request.POST['date']
    else:
        date = datetime.datetime.now()

    Income.objects.create(user=thisUser, amount=request.POST['amount'],
                           text=request.POST['text'], date=date)

    # print request.POST

    return JsonResponse({'status': 'ok'}, encoder=JSONEncoder)


@csrf_exempt
def submit_expense(request):
    """" exspense add """
    # TODO: might be fake

    thisToken = request.POST['token']
    thisUser = User.objects.filter(token__token=thisToken).get()

    if 'date' in request.POST:
        date = request.POST['date']
    else:
        date = datetime.datetime.now()

    Expense.objects.create(user=thisUser, amount=request.POST['amount'],
                           text=request.POST['text'], date=date)

    # print request.POST

    return JsonResponse({'status': 'ok'}, encoder=JSONEncoder)
