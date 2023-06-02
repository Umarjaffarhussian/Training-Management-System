from django.shortcuts import get_object_or_404, render, redirect
from django.views import View
from django.contrib import messages
from .models import Subject, Trainer, Student, StudentResult
from .forms import EditResultForm
from django.urls import reverse


class EditResultView(View):
    def get(self, request, *args, **kwargs):
        resultForm = EditResultForm()
        trainer = get_object_or_404(Trainer, admin=request.user)
        resultForm.fields['subject'].queryset = Subject.objects.filter(trainer=trainer)
        context = {
            'form': resultForm,
            'page_title': "Edit Student's Result"
        }
        return render(request, "trainer_template/edit_student_result.html", context)

    def post(self, request, *args, **kwargs):
        form = EditResultForm(request.POST)
        context = {'form': form, 'page_title': "Edit Student's Result"}
        if form.is_valid():
            try:
                students = form.cleaned_data.get('students')
                subject = form.cleaned_data.get('subject')
                test = form.cleaned_data.get('test')
                exam = form.cleaned_data.get('exam')
                # Validating
                result = StudentResult.objects.get(students=students, subject=subject)
                result.exam = exam
                result.test = test
                result.save()
                messages.success(request, "Result Updated")
                return redirect(reverse('edit_student_result'))
            except Exception as e:
                messages.warning(request, "Result Could Not Be Updated")
        else:
            messages.warning(request, "Result Could Not Be Updated")
        return render(request, "trainer_template/edit_student_result.html", context)
