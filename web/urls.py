from django.conf.urls import url, include
from django.contrib import admin

from web import views

urlpatterns = [
    url(r'^submit/expense/$', views.submit_expense, name='submit_expense'),
    url(r'^submit/income/$', views.submit_income, name='submit_income'),
]
