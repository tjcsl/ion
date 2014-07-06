""" Blocks """
from rest_framework import generics, views
from django.shortcuts import redirect, render
from intranet.apps.eighth.models import EighthBlock
from intranet.apps.auth.decorators import eighth_admin_required
from intranet.apps.eighth.serializers import EighthBlockListSerializer, EighthBlockDetailSerializer
from itertools import chain
from .common import get_startdate_fallback, get_startdate_str, parse_date, \
    eighth_confirm_view
import logging
logger = logging.getLogger(__name__)

def get_current_blocks(request=None):
    """
        Get a list of the current blocks using the startdate
        specified in the session, or defaulting to today's
        date.

    """
    if request is not None:
        d = get_startdate_fallback(request)
        s = EighthBlock.objects.filter(date__gt=d)[:1]
        logger.info("s={}".format(s))
        if len(s) > 0:
            return list(chain([s[0]], s[0].next_blocks()))
    return EighthBlock.objects.get_current_blocks()

@eighth_admin_required
def eighth_choose_block(request):
    next = request.GET.get('next', 'signup')

    blocks = get_current_blocks(request)
    return render(request, "eighth/choose_block.html", {
        "page": "eighth_admin",
        "blocks": blocks,
        "next": "/eighth/{}block/".format(next)
    })

@eighth_admin_required
def eighth_blocks_edit(request, block_id=None):
    if 'confirm' in request.POST:
        block = EighthBlock.objects.get(id=block_id)
        date = parse_date(request.POST.get('date'))
        if date != block.date:
            block.date = date
        block_letter = request.POST.get('block_letter')
        if block_letter != block.block_letter:
            block.block_letter = block_letter
        block.save()
        return redirect("/eighth/blocks/edit/?success=1")
    elif block_id is not None:
        block = EighthBlock.objects.get(id=block_id)
        return render(request, "eighth/block_edit.html", {
            "page": "eighth_admin",
            "blockobj": block,
            "block_id": block_id
        })
    else:
        blocks = get_current_blocks(request)
        return render(request, "eighth/blocks.html", {
            "page": "eighth_admin",
            "blocks": blocks,
            "date": get_startdate_str(request)
        })

@eighth_admin_required
def eighth_blocks_delete(request, block_id):
    try:
        blk = EighthBlock.objects.get(id=block_id)
    except EighthBlock.DoesNotExist:
        raise Http404

    if 'confirm' in request.POST:
        blk.delete()
        return redirect("/eighth/blocks/edit/?success=1")
    else:
        return eighth_confirm_view(request,
            "delete block {}".format(blk)
        )



@eighth_admin_required
def eighth_blocks_add(request):
    blockletters = request.POST.getlist('blocks')
    date = request.POST.get('date')

    if 'confirm' in request.POST:
        # Because of multiple checkbox wierdness
        blockletters = request.POST.get('blocks').split(',')
        blocks = []
        dtime = parse_date(date)
        for bl in blockletters:
            if len(EighthBlock.objects.filter(date=dtime, block_letter=list(bl)[0])) < 1:
                EighthBlock.objects.create(
                    date=dtime,
                    block_letter=list(bl)[0]
                )
            else:
                pass
                # The block already existed
        return redirect("/eighth/admin?success=1")
    else:
        blocks = ""
        for bl in blockletters:
            blocks += "<li>{} {} Block</li>".format(date, bl)
        return eighth_confirm_view(request,
            "register the following blocks: <ul>{}</ul>".format(blocks),
            {
                "date": date,
                "blocks": ','.join(blockletters)
            }
        )

class EighthBlockList(generics.ListAPIView):
    """API endpoint that lists all eighth blocks
    """
    queryset = EighthBlock.objects.get_current_blocks()
    serializer_class = EighthBlockListSerializer


class EighthBlockDetail(views.APIView):
    """API endpoint that shows details for an eighth block
    """
    def get(self, request, pk):
        try:
            block = EighthBlock.objects.prefetch_related("eighthscheduledactivity_set").get(pk=pk)
        except EighthBlock.DoesNotExist:
            raise Http404

        serializer = EighthBlockDetailSerializer(block, context={"request": request})
        return Response(serializer.data)

