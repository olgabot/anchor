import matplotlib.pyplot as plt
import numpy as np
import numpy.testing as npt
import pandas as pd
import pandas.util.testing as pdt
import pytest


class TestModalityEstimator(object):
    @pytest.fixture
    def step(self):
        return 1.

    @pytest.fixture
    def vmax(self):
        return 20.

    @pytest.fixture(params=[2, 3])
    def logbf_thresh(self, request):
        return request.param

    @pytest.fixture
    def estimator(self, logbf_thresh):
        from anchor.estimator import BayesianModalities, ONE_PARAMETER_MODELS, \
            TWO_PARAMETER_MODELS
        from anchor.visualize import MODALITY_TO_CMAP

        return BayesianModalities(
            one_parameter_models=ONE_PARAMETER_MODELS,
            two_parameter_models=TWO_PARAMETER_MODELS,
            logbf_thresh=logbf_thresh, model_palettes=MODALITY_TO_CMAP)

    @pytest.fixture(params=['no_na', 'with_na'])
    def event(self, request):
        x = np.arange(0, 1.1, .1)
        if request.param == 'no_na':
            return x
        elif request.param == 'with_na':
            x[x < 0.5] = np.nan
            return x

    @pytest.fixture
    def positive_control(self):
        """Randomly generated positive controls for modality estimation"""
        size = 20
        psi0 = pd.Series(np.random.uniform(0, 0.1, size=size), name='~0')
        psi1 = pd.Series(np.random.uniform(0.9, 1, size=size), name='~1')
        middle = pd.Series(np.random.uniform(0.45, 0.55, size=size),
                           name='middle')
        bimodal = pd.Series(np.concatenate([
            np.random.uniform(0, 0.05, size=size / 2),
            np.random.uniform(0.95, 1, size=size / 2)]), name='bimodal')
        df = pd.concat([psi0, psi1, middle, bimodal], axis=1)
        return df

    def test_init(self, logbf_thresh):
        from anchor import BayesianModalities, ModalityModel, MODALITY_TO_CMAP
        from anchor.estimator import ONE_PARAMETER_MODELS, \
            TWO_PARAMETER_MODELS

        estimator = BayesianModalities(
            one_parameter_models=ONE_PARAMETER_MODELS,
            two_parameter_models=TWO_PARAMETER_MODELS,
            logbf_thresh=logbf_thresh, modality_to_cmap=MODALITY_TO_CMAP)

        true_one_param_models = {k: ModalityModel(**v)
                                 for k, v in ONE_PARAMETER_MODELS.items()}

        true_two_param_models = {k: ModalityModel(**v)
                                 for k, v in TWO_PARAMETER_MODELS.items()}

        npt.assert_equal(estimator.logbf_thresh, logbf_thresh)
        pdt.assert_dict_equal(estimator.modality_to_cmap, MODALITY_TO_CMAP)
        pdt.assert_dict_equal(estimator.one_param_models,
                              true_one_param_models)
        pdt.assert_dict_equal(estimator.two_param_models,
                              true_two_param_models)

    @pytest.mark.xfail
    def test_fit_transform_greater_than1(self, estimator):
        nrows = 10
        ncols = 5
        data = pd.DataFrame(
            np.abs(np.random.randn(nrows, ncols).reshape(nrows, ncols))+10)
        estimator.fit(data)

    @pytest.mark.xfail
    def test_fit_transform_less_than1(self, estimator):
        nrows = 10
        ncols = 5
        data = pd.DataFrame(
            np.abs(np.random.randn(nrows, ncols).reshape(nrows, ncols))-10)
        estimator.fit(data)

    def test_positive_control(self, estimator, positive_control):
        """Make sure estimator correctly assigns modalities to known events"""
        log2bf = estimator.fit(positive_control)
        test = estimator.predict(log2bf)

        pdt.assert_almost_equal(test.values, test.index)

    def test_violinplot(self, estimator):
        estimator.violinplot(n=100)
        fig = plt.gcf()
        assert len(fig.axes) == len(estimator.models)
        plt.close('all')
