from django.shortcuts import render, redirect
from .models import * 
from accounts.models import *
from django.contrib.auth.models import User 
from django.core.paginator import Paginator 
from datetime import datetime, timedelta, date 
from django.core.paginator import Paginator 
from django.template import RequestContext
# KAKAO API
from TripMate.settings import KAKAO_JS_KEY
from django.db.models import Q
from accounts.models import *
from django.contrib.auth.decorators import login_required
from TripMate.settings import AWS_ACCESS_KEY_ID,AWS_SECRET_ACCESS_KEY,AWS_STORAGE_BUCKET_NAME,AWS_S3_REGION_NAME
import boto3
from boto3.session import Session
from datetime import datetime


def start(request):
    return render(request, 'feeds/start.html')

def main(request, num=0):
    alltrips = Trip.objects.all()
    mytrips = Trip.objects.all()
    mytrip = None

    # initial numbers 
    num = 0
    tot_num_m = 0  
    next_num = 0 
    before_num  = 0 
    zero = 0

    if mytrips.count() != 0:
        mytrips = mytrips.filter(user_id=request.user.id)
        tot_num = mytrips.count()
        tot_num_m = tot_num-1

        if tot_num > 0:
            num = num%tot_num

        next_num = num+1
        before_num = num-1
        print(num, "num")
        print(tot_num_m, "total num")
        zero = 0

        if mytrips.count() != 0:
            mytrip = mytrips[num]
            my_start = mytrip.start_date
            my_end = mytrip.end_date
            print(my_start)
            print(my_end)
            
            #date or 조건 지정하기
            q = Q()
            q.add(Q(start_date__lte=my_start)&~Q(end_date__lte=my_start),q.OR)
            q.add(~Q(start_date__gt=my_end)&Q(end_date__gte=my_end),q.OR)
            q.add(Q(start_date__gte=my_start)&Q(end_date__lte=my_end),q.OR)
            q.add(Q(start_date__lte=my_start)&Q(end_date__gte=my_end),q.OR)

            alltrips = Trip.objects.all().filter(q)
            temptrips = alltrips.filter(place=mytrip.place).exclude(user_id=request.user.id)
            print(alltrips)
            print(temptrips)

            alltrips = list()
            print(alltrips, "alltrip을 check해 보아요")

            for trip in temptrips:
                if Profile.objects.all().count() != 0:
                    follow_from = Profile.objects.get(user_id=request.user.id)
                    follow_to = Profile.objects.get(user_id=trip.user.id)
                    place = Trip.objects.get(id=trip.id).place
                    print(follow_from)
                    print(follow_to)

                    follow_already = Follow.objects.filter(follow_from=follow_from, follow_to=follow_to, place=place)

                    if follow_already.count() != 0:
                        print("follow 존재")
                    else:
                        alltrips.append(trip)
                else:
                    alltrips.append(trip)

            print(alltrips)
    return render(request, 'feeds/main.html',
    {'mytrip':mytrip,'mytrips':mytrips,'alltrips':alltrips,
    'num':num,'tot_num_m':tot_num_m,'next_num':next_num,'before_num':before_num, 'zero':zero})

@login_required(login_url="/accounts/login/")
def mypage(request):
    trips = Trip.objects.all().filter(user_id=request.user.id)
    if request.method == 'POST':
        print(request.user)
        place_v = request.POST['place']
        start_date = request.POST['start_date']
        end_date = request.POST['end_date']
        mynum = request.POST['mynum']
        brief_info = request.POST['brief_info']
        keyword1 = request.POST.get('keyword1',False)
        keyword2 = request.POST.get('keyword2',False)
        keyword3 = request.POST.get('keyword3',False)
        mate_num = request.POST['mate_num']
        mate_age = request.POST['mate_age']
        mate_gen = request.POST['mate_gen']
        itier_lat = request.POST['itier_lat']
        itier_long = request.POST['itier_long']
        Trip.objects.create(user_id=request.user.id,itier_name='x',itier_lat=itier_lat,itier_long=itier_long,place=place_v,my_num=mynum,start_date=start_date,end_date=end_date,bref_info=brief_info,keyword1=keyword1,keyword2=keyword2,keyword3=keyword3,want_gender=mate_gen,want_age=mate_age,want_num=mate_num)
        return render(request, 'feeds/mypage.html')
    return render(request, 'feeds/mypage.html',{'trips':trips})


def mypage_detail(request,place):
    trips = Trip.objects.all().filter(user_id=request.user.id,place=place)
    print(trips)
    return render(request, 'feeds/mypage_detail.html',{'trips':trips,'KAKAO_JS_KEY':KAKAO_JS_KEY})

def mypage_detail_edit(request,place):
    trips = Trip.objects.all().filter(user_id=request.user.id,place=place)
    return render(request, 'feeds/mypage_detail_edit.html',{'trips':trips,'KAKAO_JS_KEY':KAKAO_JS_KEY})

def mypage_edit(request):
    myInfo = Profile.objects.all().get(user_id=request.user.id)
    if request.method == "POST":
        file_to_upload = request.FILES.get('img')
        session = Session(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_S3_REGION_NAME
        )
        s3 = session.resource('s3')
        now = datetime.now().strftime("%Y%H%M%S")
        img_object = s3.Bucket(AWS_STORAGE_BUCKET_NAME).put_object(
             Key = str(request.user.id)+now,
             Body = file_to_upload
        )
        s3_url = "https://tripmate-storage.s3.ap-northeast-2.amazonaws.com/"
        userProfile = Profile.objects.all().get(user_id=request.user.id)
        userProfile.name=request.POST['name']
        userProfile.nickname = request.POST['nickname']
        userProfile.gender = GENDER_OPTION[1] if request.POST['gender'] == 'male' else GENDER_OPTION[0]
        userProfile.age = request.POST['age']
        # userProfile.photo =  s3_url + str(request.user.id)+now
        userProfile.save()
    
        return redirect('mypage')
    return render(request, "feeds/mypage_edit.html",{"myInfo":myInfo})


def select_place(request):
    mytrip = Trip.objects.all().filter(user_id=request.user.id)
    jeju ='x'
    yeosu ='x'
    jeonju ='x'
    if mytrip.filter(place='제주'):
        jeju ='o'
    if mytrip.filter(place='여수'):
        yeosu ='o'
    if mytrip.filter(place='전주'):
        jeonju ='o'
    
    return render(request, 'feeds/select_place.html', {'jeju':jeju,'yeosu':yeosu,'jeonju':jeonju})


def select_detail_1(request,place):
    if(request.POST):
        return render(request, 'feeds/select_place_1.html',{"place":place,"KAKAO_JS_KEY":KAKAO_JS_KEY})

    return render(request, 'feeds/select_place_1.html',{"place":place,"KAKAO_JS_KEY":KAKAO_JS_KEY})
