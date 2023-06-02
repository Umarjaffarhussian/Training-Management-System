import json
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,redirect, render)
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from .forms import *
from .models import *


def trainer_home(request):
    trainer = get_object_or_404(Trainer, admin=request.user)
    total_students = Student.objects.filter(course=trainer.course).count()
    total_leave = LeaveReportTrainer.objects.filter(trainer=trainer).count()
    subjects = Subject.objects.filter(trainer=trainer)
    total_subject = subjects.count()
    attendance_list = Attendance.objects.filter(subject__in=subjects)
    total_attendance = attendance_list.count()
    attendance_list = []
    subject_list = []
    for subject in subjects:
        attendance_count = Attendance.objects.filter(subject=subject).count()
        subject_list.append(subject.name)
        attendance_list.append(attendance_count)
    context = {
        'page_title': 'Trainer Panel - ' + str(trainer.admin.last_name) + ' (' + str(trainer.course) + ')',
        'total_students': total_students,
        'total_attendance': total_attendance,
        'total_leave': total_leave,
        'total_subject': total_subject,
        'subject_list': subject_list,
        'attendance_list': attendance_list
    }
    return render(request, 'trainer_template/home_content.html', context)


def trainer_take_attendance(request):
    trainer = get_object_or_404(Trainer, admin=request.user)
    subjects = Subject.objects.filter(trainer_id=trainer)
    sessions = Session.objects.all()
    context = {
        'subjects': subjects,
        'sessions': sessions,
        'page_title': 'Take Attendance'
    }
    return render(request, 'trainer_template/trainer_take_attendance.html', context)


@csrf_exempt
def get_students(request):
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    try:
        subject = get_object_or_404(Subject, id=subject_id)
        session = get_object_or_404(Session, id=session_id)
        students = Student.objects.filter(
            course_id=subject.course.id, session=session)
        student_data = []
        for student in students:
            data = {
                    "id": student.id,
                    "name": student.admin.last_name + " " + student.admin.first_name
                    }
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return e


@csrf_exempt
def save_attendance(request):
    student_data = request.POST.get('student_ids')
    date = request.POST.get('date')
    subject_id = request.POST.get('subject')
    session_id = request.POST.get('session')
    students = json.loads(student_data)
    try:
        session = get_object_or_404(Session, id=session_id)
        subject = get_object_or_404(Subject, id=subject_id)
        attendance = Attendance(session=session, subject=subject, date=date)
        attendance.save()

        for student_dict in students:
            student = get_object_or_404(Student, id=student_dict.get('id'))
            attendance_report = AttendanceReport(student=student, attendance=attendance, status=student_dict.get('status'))
            attendance_report.save()
    except Exception as e:
        return None

    return HttpResponse("OK")


def trainer_update_attendance(request):
    trainer = get_object_or_404(Trainer, admin=request.user)
    subjects = Subject.objects.filter(trainer_id=trainer)
    sessions = Session.objects.all()
    context = {
        'subjects': subjects,
        'sessions': sessions,
        'page_title': 'Update Attendance'
    }

    return render(request, 'trainer_template/trainer_update_attendance.html', context)


@csrf_exempt
def get_student_attendance(request):
    attendance_date_id = request.POST.get('attendance_date_id')
    try:
        date = get_object_or_404(Attendance, id=attendance_date_id)
        attendance_data = AttendanceReport.objects.filter(attendance=date)
        student_data = []
        for attendance in attendance_data:
            data = {"id": attendance.student.admin.id,
                    "name": attendance.student.admin.last_name + " " + attendance.student.admin.first_name,
                    "status": attendance.status}
            student_data.append(data)
        return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)
    except Exception as e:
        return e


@csrf_exempt
def update_attendance(request):
    student_data = request.POST.get('student_ids')
    date = request.POST.get('date')
    students = json.loads(student_data)
    try:
        attendance = get_object_or_404(Attendance, id=date)

        for student_dict in students:
            student = get_object_or_404(
                Student, admin_id=student_dict.get('id'))
            attendance_report = get_object_or_404(AttendanceReport, student=student, attendance=attendance)
            attendance_report.status = student_dict.get('status')
            attendance_report.save()
    except Exception as e:
        return None

    return HttpResponse("OK")


def trainer_apply_leave(request):
    form = LeaveReportTrainerForm(request.POST or None)
    trainer = get_object_or_404(Trainer, admin_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportTrainer.objects.filter(trainer=trainer),
        'page_title': 'Apply for Leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.trainer = trainer
                obj.save()
                messages.success(
                    request, "Application for leave has been submitted for review")
                return redirect(reverse('trainer_apply_leave'))
            except Exception:
                messages.error(request, "Could not apply!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "trainer_template/trainer_apply_leave.html", context)


def trainer_feedback(request):
    form = FeedbackTrainerForm(request.POST or None)
    trainer = get_object_or_404(Trainer, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackTrainer.objects.filter(trainer=trainer),
        'page_title': 'Add Feedback'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.trainer = trainer
                obj.save()
                messages.success(request, "Feedback submitted for review")
                return redirect(reverse('trainer_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "trainer_template/trainer_feedback.html", context)


def trainer_view_profile(request):
    trainer = get_object_or_404(Trainer, admin=request.user)
    form = TrainerEditForm(request.POST or None, request.FILES or None,instance=trainer)
    context = {'form': form, 'page_title': 'View/Update Profile'}
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                admin = trainer.admin
                if password != None:
                    admin.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    admin.profile_pic = passport_url
                admin.first_name = first_name
                admin.last_name = last_name
                admin.address = address
                admin.gender = gender
                admin.save()
                trainer.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('trainer_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
                return render(request, "trainer_template/trainer_view_profile.html", context)
        except Exception as e:
            messages.error(
                request, "Error Occured While Updating Profile " + str(e))
            return render(request, "trainer_template/trainer_view_profile.html", context)

    return render(request, "trainer_template/trainer_view_profile.html", context)


@csrf_exempt
def trainer_fcmtoken(request):
    token = request.POST.get('token')
    try:
        trainer_user = get_object_or_404(CustomUser, id=request.user.id)
        trainer_user.fcm_token = token
        trainer_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def trainer_view_notification(request):
    trainer = get_object_or_404(Trainer, admin=request.user)
    notifications = NotificationTrainer.objects.filter(trainer=trainer)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "trainer_template/trainer_view_notification.html", context)


def trainer_add_result(request):
    trainer = get_object_or_404(Trainer, admin=request.user)
    subjects = Subject.objects.filter(trainer=trainer)
    sessions = Session.objects.all()
    context = {
        'page_title': 'Result Upload',
        'subjects': subjects,
        'sessions': sessions
    }
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_list')
            subject_id = request.POST.get('subject')
            test = request.POST.get('test')
            exam = request.POST.get('exam')
            student = get_object_or_404(Student, id=student_id)
            subject = get_object_or_404(Subject, id=subject_id)
            try:
                data = StudentResult.objects.get(
                    student=student, subject=subject)
                data.exam = exam
                data.test = test
                data.save()
                messages.success(request, "Scores Updated")
            except:
                result = StudentResult(student=student, subject=subject, test=test, exam=exam)
                result.save()
                messages.success(request, "Scores Saved")
        except Exception as e:
            messages.warning(request, "Error Occured While Processing Form")
    return render(request, "trainer_template/trainer_add_result.html", context)


@csrf_exempt
def fetch_student_result(request):
    try:
        subject_id = request.POST.get('subject')
        student_id = request.POST.get('student')
        student = get_object_or_404(Student, id=student_id)
        subject = get_object_or_404(Subject, id=subject_id)
        result = StudentResult.objects.get(student=student, subject=subject)
        result_data = {
            'exam': result.exam,
            'test': result.test
        }
        return HttpResponse(json.dumps(result_data))
    except Exception as e:
        return HttpResponse('False')
