from GEMEditor.analysis.duplicates import *
from GEMEditor.cobraClasses import Reaction, Metabolite
from GEMEditor.data_classes import Annotation
from GEMEditor.evidence_class import Evidence
import itertools
import pytest


def test_get_reaction_set_wo_directionality():
    reaction = Reaction("React1")
    metabolite1 = Metabolite("Met1")
    metabolite2 = Metabolite("Met2")
    stoichiometry = {metabolite1: -1,
                     metabolite2: 1}
    reaction.add_metabolites(stoichiometry)
    assert get_reaction_set(reaction, remove_directionality=True) == \
           frozenset([frozenset([(metabolite1, 1)]), frozenset([(metabolite2, 1)])])


def test_get_reaction_set_with_directionality():
    reaction = Reaction("React1")
    metabolite1 = Metabolite("Met1")
    metabolite2 = Metabolite("Met2")
    stoichiometry = {metabolite1: -1,
                     metabolite2: 1}
    reaction.add_metabolites(stoichiometry)
    assert get_reaction_set(reaction, remove_directionality=False) == \
           frozenset([frozenset([(metabolite1, -1)]), frozenset([(metabolite2, 1)])])


def test_group_duplicate_reactions():
    reaction1 = Reaction("React1")
    reaction2 = Reaction("React2")
    metabolite1 = Metabolite("Met1")
    metabolite2 = Metabolite("Met2")
    reaction1.add_metabolites({metabolite1: -1,
                               metabolite2: 1})
    reaction2.add_metabolites({metabolite1: 1,
                               metabolite2: -1})
    result = group_duplicate_reactions([reaction1, reaction2])
    assert len(result) == 1
    assert reaction1 in list(result.values())[0]
    assert reaction2 in list(result.values())[0]


def test_group_duplicates_reactions_different_reactions():
    reaction1 = Reaction("React1")
    reaction2 = Reaction("React2")
    metabolite1 = Metabolite("Met1")
    metabolite2 = Metabolite("Met2")
    reaction1.add_metabolites({metabolite1: -1,
                               metabolite2: 1})
    reaction2.add_metabolites({metabolite1: 1,
                               metabolite2: -2})
    result = group_duplicate_reactions([reaction1, reaction2])
    assert len(result) == 2
    assert all(len(x) == 1 for x in itertools.chain(result.values()))
    assert reaction1 in itertools.chain(*result.values())
    assert reaction2 in itertools.chain(*result.values())


class Test_get_metabolites_same_compartment:

    def test_sorting_of_compartments(self):
        metabolite1 = Metabolite(compartment=None)
        metabolite2 = Metabolite(compartment="c")
        metabolite3 = Metabolite(compartment="c")

        grouping = get_metabolites_same_compartment([metabolite1, metabolite2, metabolite3])

        assert len(grouping) == 2
        assert set(grouping["c"]) == set([metabolite2, metabolite3])
        assert grouping[""] == [metabolite1]


class Test_get_duplicated_metabolites:

    def test_using_annotations(self):
        met1 = Metabolite()
        met2 = Metabolite()
        met3 = Metabolite()

        met1.annotation.add(Annotation(collection="chebi", identifier="CHEBI:35128"))
        met2.annotation.add(Annotation(collection="chebi", identifier="CHEBI:35128"))
        met3.annotation.add(Annotation(collection="chebi", identifier="CHEBI:17676"))

        # Group items with overlapping annotations
        groups = get_duplicated_metabolites([met1, met2, met3])
        assert len(groups) == 1
        assert set(groups.pop()) == set([met1, met2])

    def test_using_database_mapping(self):
        met1 = Metabolite()
        met2 = Metabolite()
        met3 = Metabolite()

        datbase_mapping = {met1: "1",
                           met2: "1",
                           met3: "2"}

        # Group items mapping to the same datbase entry
        groups = get_duplicated_metabolites([met1, met2, met3], datbase_mapping)
        assert len(groups) == 1
        assert set(groups.pop()) == set([met1, met2])


class Test_merge_metabolites:

    def test_merging_metabolites(self):
        met1 = Metabolite("m1")
        met2 = Metabolite("m2")
        met3 = Metabolite("m3")

        reaction = Reaction()
        original_metabolites = {met1: -1, met2: 1}
        reaction.add_metabolites(original_metabolites)

        merged = merge_metabolites([met1, met3], met3)

        # Check that met1 has been substituted with met3
        assert merged == [met1]
        assert reaction.metabolites == {met3: -1, met2: 1}

    def test_merging_evidences(self):
        met1 = Metabolite("m1")
        evidence1 = Evidence()
        evidence1.set_entity(met1)
        met2 = Metabolite("m2")

        assert evidence1 in met1.evidences

        merge_metabolites([met1, met2], met2)

        assert evidence1 not in met1.evidences
        assert evidence1 in met2.evidences

