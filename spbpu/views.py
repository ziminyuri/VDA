import os
import random

from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import DetailView, View

from services.model import create_model, get_model_data
from services.pairs_of_options import (absolute_value_in_str, create_files,
                                       data_of_winners, make_question,
                                       write_answer)

from services.history import checking_already_has_answer
from services.graph import get_graph_pacom, get_graph_snod


from services.snod_original import get_original_snod_question, write_original_snod_answer, \
    get_winners_from_model_original_snod, get_context_history_answer_original_snod
from services.settings import settingsPACOMCreate, settingsOrigianlSnodCreate
from spbpu.models import (HistoryAnswer, Model, Option, PairsOfOptions)
from Verbal_Decision_Analysis.settings import MEDIA_ROOT

from services.statistics import get_statistics, built_statistics, get_statistics_original_snod,  get_table_context, \
    built_statistics_number_question
from django.contrib.auth.mixins import LoginRequiredMixin

if 'DATABASE_URL' in os.environ:
    path_img = 'glacial-everglades-54891.herokuapp.com'










