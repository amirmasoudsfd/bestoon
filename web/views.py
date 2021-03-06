# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import random
import string
from json import JSONEncoder

from datetime import datetime

from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Sum, Count

from web.models import *
import requests

from django.core import serializers
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.hashers import make_password
from django.db.models import Sum, Count
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password, check_password
from .models import User, Token, Expense, Income, Passwordresetcodes

from django.views.decorators.http import require_POST

from .utils import grecaptcha_verify, RateLimited, get_client_ip

# create random string for Toekn
random_str = lambda N: ''.join(
    random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(N))


def index(request):
    context = {}
    return render(request, 'index.html', context)


@csrf_exempt
def news(request):
    news = News.objects.all().order_by('-date')[:11]
    news_serialized = serializers.serialize("json", news)
    # return JsonResponse(news_serialized, encoder=JSONEncoder, safe=False)
    return HttpResponse(news_serialized)


@csrf_exempt
@require_POST
def query_incomes(request):
    thisToken = request.POST['token']
    incomesNumber = request.POST.get('count', 11)
    thisUser = User.objects.filter(token__token=thisToken).get()

    incomes = Income.objects.filter(user=thisUser).order_by('-date')[:incomesNumber]
    incomes_serialized = serializers.serialize("json", incomes)

    return HttpResponse(incomes_serialized)


@csrf_exempt
@require_POST
def query_expenses(request):
    thisToken = request.POST['token']
    expensesNumber = request.POST.get('count', 11)

    thisUser = User.objects.filter(token__token=thisToken).get()

    expenses = Expense.objects.filter(user=thisUser).order_by('-date')[:expensesNumber]
    expenses_serialized = serializers.serialize("json", expenses)

    return JsonResponse(expenses_serialized, encoder=JSONEncoder)


@csrf_exempt
@require_POST
def generalstat(request):
    # TODO: get a duration (from - to), default 1 month

    thisToken = request.POST['token']
    thisUser = User.objects.filter(token__token=thisToken).get()

    income = Income.objects.filter(user=thisUser).aggregate(Count('amount'), Sum('amount'))
    expense = Expense.objects.filter(user=thisUser).aggregate(Count('amount'), Sum('amount'))

    context = {'expense': expense, 'income': income}

    return JsonResponse(context, encoder=JSONEncoder)


@csrf_exempt
@require_POST
# @RateLimited(2)
def login(request):
    if request.POST.has_key('username') and request.POST.has_key('password'):
        username, password = request.POST['username'], request.POST['password']
        try:
            thisUser = User.objects.get(username=username)
        except ObjectDoesNotExist:
            context = {'result': 'error'}
            return JsonResponse(context, encoder=JSONEncoder)

        if check_password(password, thisUser.password):
            thisToken = Token.objects.get(user=thisUser)
            token = thisToken.token
            context = {'result': 'ok', 'token': token}
            return JsonResponse(context, encoder=JSONEncoder)
        else:
            context = {'result': 'error'}
            return JsonResponse(context, encoder=JSONEncoder)


def register(request):
    if request.POST.has_key('requestcode'):
        # form is filled. if not spam, generate code and save in db, wait for email confirmation, return message
        # is this spam? check reCaptcha
        if not grecaptcha_verify(request):  # captcha was not correct
            context = {
                'message': 'کپچای گوگل درست وارد نشده بود. شاید ربات هستید؟ کد یا کلیک یا تشخیص عکس زیر فرم را درست پر کنید. ببخشید که فرم به شکل اولیه برنگشته!'}  # TODO: forgot password
            return render(request, 'register.html', context)

        # duplicate email
        if User.objects.filter(email=request.POST['email']).exists():
            context = {
                'message': 'متاسفانه این ایمیل قبلا استفاده شده است. در صورتی که این ایمیل شما است، از صفحه ورود گزینه فراموشی پسورد رو انتخاب کنین. ببخشید که فرم ذخیره نشده. درست می شه'}  # TODO: forgot password
            # TODO: keep the form data
            return render(request, 'register.html', context)
        # if user does not exists
        if not User.objects.filter(username=request.POST['username']).exists():
            code = get_random_string(length=32)
            now = datetime.now()
            email = request.POST['email']
            password = make_password(request.POST['password'])
            username = request.POST['username']
            temporarycode = Passwordresetcodes(
                email=email, time=now, code=code, username=username, password=password)
            temporarycode.save()
            # message = PMMail(api_key=settings.POSTMARK_API_TOKEN,
            #                 subject="فعالسازی اکانت بستون",
            #                 sender="sefidian@sefidian.com",
            #                 to=email,
            #                 text_body=" برای فعال کردن اکانت بستون خود روی لینک روبرو کلیک کنید: {}?code={}".format(
            #                     request.build_absolute_uri('/accounts/register/'), code),
            #                 tag="account request")
            # message.send()
            message = 'ایمیلی حاوی لینک فعال سازی اکانت به شما فرستاده شده، لطفا پس از چک کردن ایمیل، روی لینک کلیک کنید.'
            message = 'قدیم ها ایمیل فعال سازی می فرستادیم ولی الان شرکتش ما رو تحریم کرده (: پس راحت و بی دردسر'
            body = " برای فعال کردن اکانت بستون خود روی لینک روبرو کلیک کنید: <a href=\"{}?code={}\">لینک رو به رو</a> ".format(
                request.build_absolute_uri('/accounts/register/'), code)
            message = message + body
            context = {
                'message': message}
            return render(request, 'index.html', context)
        else:
            context = {
                'message': 'متاسفانه این نام کاربری قبلا استفاده شده است. از نام کاربری دیگری استفاده کنید. ببخشید که فرم ذخیره نشده. درست می شه'}  # TODO: forgot password
            # TODO: keep the form data
            return render(request, 'register.html', context)
    elif request.GET.has_key('code'):  # user clicked on code
        code = request.GET['code']
        if Passwordresetcodes.objects.filter(code=code).exists():
            # if code is in temporary db, read the data and create the user
            new_temp_user = Passwordresetcodes.objects.get(code=code)
            newuser = User.objects.create(username=new_temp_user.username, password=new_temp_user.password,
                                          email=new_temp_user.email)
            this_token = get_random_string(length=48)
            token = Token.objects.create(user=newuser, token=this_token)
            # delete the temporary activation code from db
            Passwordresetcodes.objects.filter(code=code).delete()
            context = {
                'message': 'اکانت شما ساخته شد. توکن شما {} است. آن را ذخیره کنید چون دیگر نمایش داده نخواهد شد! جدی!'.format(
                    this_token)}
            return render(request, 'index.html', context)
        else:
            context = {
                'message': 'این کد فعال سازی معتبر نیست. در صورت نیاز دوباره تلاش کنید'}
            return render(request, 'register.html', context)
    else:
        context = {'message': ''}
        return render(request, 'register.html', context)


# return username based on sent POST Token


@csrf_exempt
@require_POST
def submit_income(request):
    """" exspense add """
    # TODO: might be fake

    thisToken = request.POST['token']
    thisUser = User.objects.filter(token__token=thisToken).get()

    if 'date' in request.POST:
        date = request.POST['date']
    else:
        date = datetime.now()

    Income.objects.create(user=thisUser, amount=request.POST['amount'],
                          text=request.POST['text'], date=date)

    # print request.POST

    return JsonResponse({'status': 'ok'}, encoder=JSONEncoder)


@csrf_exempt
@require_POST
def submit_expense(request):
    """" exspense add """
    # TODO: might be fake

    thisToken = request.POST['token']
    thisUser = User.objects.filter(token__token=thisToken).get()

    if 'date' in request.POST:
        date = request.POST['date']
    else:
        date = datetime.now()

    Expense.objects.create(user=thisUser, amount=request.POST['amount'],
                           text=request.POST['text'], date=date)

    # print request.POST

    return JsonResponse({'status': 'ok'}, encoder=JSONEncoder)
