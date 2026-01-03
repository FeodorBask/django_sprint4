from django import forms
from .models import Post, Category, Location, Comment
from django.utils import timezone


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'text', 'pub_date', 'image', 'location', 'category']
        widgets = {
            'pub_date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control'
                }
            ),
            'text': forms.Textarea(attrs={
                'rows': 10,
                'class': 'form-control',
                'placeholder': 'Текст публикации'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Заголовок публикации'
            }),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'location': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'pub_date': 'Установите дату и время публикации',
            'image': 'Загрузите изображение',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(
            is_published=True
        )
        self.fields['location'].queryset = Location.objects.filter(
            is_published=True
        )
        if not self.instance.pk:
            time = timezone.now()
            self.fields['pub_date'].initial = time.strftime('%Y-%m-%dT%H:%M')


class PostDeleteForm(forms.Form):
    confirm = forms.BooleanField(
        required=True,
        label='Подтвердить удаление',
        help_text='Отметьте, чтобы подтвердить удаление публикации'
    )


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Текст комментария'
            }),
        }
        labels = {
            'text': '',
        }
    

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
        return instance


class CommentEditForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control'
            }),
        }
