from django.shortcuts import render
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Source
from .forms import PersonalSourceForm

@login_required
def manage_sources(request):
    sources = Source.objects.filter(user=request.user)

    if request.method == 'POST':
        form = PersonalSourceForm(request.POST)
        if form.is_valid():
            new_source = form.save(commit=False)
            new_source.user = request.user
            new_source.save()
            return redirect('manage_sources')
    else:
        form = PersonalSourceForm()

    return render(request, 'news/manage_sources.html', {
        'sources': sources,
        'form': form,
    })

@login_required
def delete_source(request, pk):
    source = get_object_or_404(Source, pk=pk, user=request.user)
    if request.method == 'POST':
        source.delete()
    return redirect('manage_sources')
