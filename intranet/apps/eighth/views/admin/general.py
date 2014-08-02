from django.contrib import messages
from django.contrib.formtools.wizard.views import SessionWizardView
from django.shortcuts import render, redirect
from ....auth.decorators import eighth_admin_required
from ...forms.admin import BlockSelectionForm, ActivitySelectionForm


@eighth_admin_required
def eighth_admin_index_view(request):
    return render(request, "eighth/admin/index.html", {})


class EighthAdminExampleWizard(SessionWizardView):
    FORMS = [
        ("block", BlockSelectionForm),
        ("activity", ActivitySelectionForm)
    ]

    TEMPLATES = {
        "block": "eighth/admin/example_form.html",
        "activity": "eighth/admin/example_form.html"
    }

    def get_template_names(self):
        return [self.TEMPLATES[self.steps.current]]

    def get_form_kwargs(self, step):
        kwargs = {}
        if step == "activity":
            block = self.get_cleaned_data_for_step("block")["block"]
            kwargs.update({"block": block})
        return kwargs

    def done(self, form_list, **kwargs):
        messages.info(self.request, "Successfully did something")

        return redirect("eighth_admin_index")
