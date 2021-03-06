import numpy as np
import pandas as pd
from scipy.sparse import issparse
from matplotlib import pyplot as pl
from matplotlib import rcParams

from .. import utils
from ...utils import doc_params
from ... import logging as logg
from ..anndata import scatter, ranking
from ..utils import timeseries, timeseries_subplot, timeseries_as_heatmap
from ..docs import doc_scatter_bulk, doc_show_save_ax


# ------------------------------------------------------------------------------
# PCA
# ------------------------------------------------------------------------------


@doc_params(scatter_bulk=doc_scatter_bulk, show_save_ax=doc_show_save_ax)
def pca(adata, **params):
    """\
    Plot PCA results.

    The parameters are the ones of the scatter plot. Call pca_ranking separately
    if you want to change the default settings.

    Parameters
    ----------
    adata : :class:`~anndata.AnnData`
        Annotated data matrix.
    color : string or list of strings, optional (default: `None`)
        Keys for observation/cell annotation either as list `["ann1", "ann2"]` or
        string `"ann1,ann2,..."`.
    use_raw : `bool`, optional (default: `True`)
        Use `raw` attribute of `adata` if present.
    {scatter_bulk}
    show : bool, optional (default: `None`)
         Show the plot, do not return axis.
    save : `bool` or `str`, optional (default: `None`)
        If `True` or a `str`, save the figure. A string is appended to the
        default filename. Infer the filetype if ending on {{'.pdf', '.png', '.svg'}}.
    """
    show = params['show'] if 'show' in params else None
    if 'show' in params: del params['show']
    pca_scatter(adata, **params, show=False)
    pca_loadings(adata, show=False)
    pca_variance_ratio(adata, show=show)


@doc_params(scatter_bulk=doc_scatter_bulk, show_save_ax=doc_show_save_ax)
def pca_scatter(
        adata,
        color=None,
        use_raw=True,
        sort_order=True,
        alpha=None,
        groups=None,
        components=None,
        projection='2d',
        legend_loc='right margin',
        legend_fontsize=None,
        legend_fontweight=None,
        color_map=None,
        palette=None,
        right_margin=None,
        size=None,
        title=None,
        show=None,
        save=None,
        ax=None):
    """\
    Scatter plot in PCA coordinates.

    Parameters
    ----------
    adata : :class:`~anndata.AnnData`
        Annotated data matrix.
    color : string or list of strings, optional (default: `None`)
        Keys for observation/cell annotation either as list `["ann1", "ann2"]` or
        string `"ann1,ann2,..."`.
    use_raw : `bool`, optional (default: `True`)
        Use `raw` attribute of `adata` if present.
    {scatter_bulk}
    show : bool, optional (default: `None`)
         Show the plot, do not return axis.
    save : `bool` or `str`, optional (default: `None`)
        If `True` or a `str`, save the figure. A string is appended to the
        default filename. Infer the filetype if ending on {{'.pdf', '.png', '.svg'}}.
    ax : matplotlib.Axes
         A matplotlib axes object.

    Returns
    -------
    If `show==False` a `matplotlib.Axis` or a list of it.
    """
    axs = scatter(
        adata,
        basis='pca',
        color=color,
        use_raw=use_raw,
        sort_order=sort_order,
        alpha=alpha,
        groups=groups,
        components=components,
        projection=projection,
        legend_loc=legend_loc,
        legend_fontsize=legend_fontsize,
        legend_fontweight=legend_fontweight,
        color_map=color_map,
        palette=palette,
        right_margin=right_margin,
        size=size,
        title=title,
        show=False,
        save=False, ax=ax)
    utils.savefig_or_show('pca_scatter', show=show, save=save)
    if show == False: return axs


def pca_loadings(adata, components=None, show=None, save=None):
    """Rank genes according to contributions to PCs.

    Parameters
    ----------
    adata : :class:`~anndata.AnnData`
        Annotated data matrix.
    components : str or list of integers, optional
        For example, ``'1,2,3'`` means ``[1, 2, 3]``, first, second, third
        principal component.
    show : bool, optional (default: `None`)
        Show the plot, do not return axis.
    save : `bool` or `str`, optional (default: `None`)
        If `True` or a `str`, save the figure. A string is appended to the
        default filename. Infer the filetype if ending on {{'.pdf', '.png', '.svg'}}.
    """
    if components is None: components = [1, 2, 3]
    elif isinstance(components, str): components = components.split(',')
    components = np.array(components) - 1
    ranking(adata, 'varm', 'PCs', indices=components)
    utils.savefig_or_show('pca_loadings', show=show, save=save)


def pca_variance_ratio(adata, log=False, show=None, save=None):
    """Plot the variance ratio.

    Parameters
    ----------
    show : bool, optional (default: `None`)
         Show the plot, do not return axis.
    save : `bool` or `str`, optional (default: `None`)
        If `True` or a `str`, save the figure. A string is appended to the
        default filename. Infer the filetype if ending on {{'.pdf', '.png', '.svg'}}.
    """
    ranking(adata, 'uns', 'variance_ratio', dictionary='pca', labels='PC', log=log)
    utils.savefig_or_show('pca_variance_ratio', show=show, save=save)


# ------------------------------------------------------------------------------
# Subgroup identification and ordering - clustering, pseudotime, branching
# and tree inference tools
# ------------------------------------------------------------------------------


def dpt_timeseries(adata, color_map=None, show=None, save=None, as_heatmap=True):
    """Heatmap of pseudotime series.

    Parameters
    ----------
    as_heatmap : bool (default: False)
        Plot the timeseries as heatmap.
    """
    if adata.n_vars > 100:
        logg.warn('Plotting more than 100 genes might take some while,'
                  'consider selecting only highly variable genes, for example.')
    # only if number of genes is not too high
    if as_heatmap:
        # plot time series as heatmap, as in Haghverdi et al. (2016), Fig. 1d
        timeseries_as_heatmap(adata.X[adata.obs['dpt_order_indices'].values],
                              var_names=adata.var_names,
                              highlightsX=adata.uns['dpt_changepoints'],
                              color_map=color_map)
    else:
        # plot time series as gene expression vs time
        timeseries(adata.X[adata.obs['dpt_order_indices'].values],
                   var_names=adata.var_names,
                   highlightsX=adata.uns['dpt_changepoints'],
                   xlim=[0, 1.3*adata.X.shape[0]])
    pl.xlabel('dpt order')
    utils.savefig_or_show('dpt_timeseries', save=save, show=show)


def dpt_groups_pseudotime(adata, color_map=None, palette=None, show=None, save=None):
    """Plot groups and pseudotime."""
    pl.figure()
    pl.subplot(211)
    timeseries_subplot(adata.obs['dpt_groups'].cat.codes,
                       time=adata.obs['dpt_order'].values,
                       color=np.asarray(adata.obs['dpt_groups']),
                       highlightsX=adata.uns['dpt_changepoints'],
                       ylabel='dpt groups',
                       yticks=(np.arange(len(adata.obs['dpt_groups'].cat.categories), dtype=int)
                                     if len(adata.obs['dpt_groups'].cat.categories) < 5 else None),
                       palette=palette)
    pl.subplot(212)
    timeseries_subplot(adata.obs['dpt_pseudotime'].values,
                       time=adata.obs['dpt_order'].values,
                       color=adata.obs['dpt_pseudotime'].values,
                       xlabel='dpt order',
                       highlightsX=adata.uns['dpt_changepoints'],
                       ylabel='pseudotime',
                       yticks=[0, 1],
                       color_map=color_map)
    utils.savefig_or_show('dpt_groups_pseudotime', save=save, show=show)


@doc_params(show_save_ax=doc_show_save_ax)
def rank_genes_groups(adata, groups=None, n_genes=20, gene_symbols=None, key=None, fontsize=8,
                      n_panels_per_row=4, show=None, save=None, ax=None):
    """\
    Plot ranking of genes.

    Parameters
    ----------
    adata : :class:`~anndata.AnnData`
        Annotated data matrix.
    groups : `str` or `list` of `str`
        The groups for which to show the gene ranking.
    gene_symbols : `str`
        Key for field in `.var` that stores gene symbols if you do not want to
        use `.var_names`.
    n_genes : `int`, optional (default: 20)
        Number of genes to show.
    fontsize : `int`, optional (default: 8)
        Fontsize for gene names.
    n_panels_per_row: `int`, optional (default: 4)
        Number of panels shown per row.
    {show_save_ax}
    """
    if key is None:
        key = 'rank_genes_groups'
    groups_key = str(adata.uns[key]['params']['groupby'])
    reference = str(adata.uns[key]['params']['reference'])
    group_names = (adata.uns[key]['names'].dtype.names
                   if groups is None else groups)
    # one panel for each group
    n_panels = len(group_names)
    # set up the figure
    n_panels_x = n_panels_per_row
    n_panels_y = np.ceil(len(group_names) / n_panels_x).astype(int)

    from matplotlib import gridspec
    fig = pl.figure(figsize=(n_panels_x * rcParams['figure.figsize'][0],
                             n_panels_y * rcParams['figure.figsize'][1]))
    left = 0.2/n_panels_x
    bottom = 0.13/n_panels_y
    gs = gridspec.GridSpec(nrows=n_panels_y,
                           ncols=n_panels_x,
                           left=left,
                           right=1-(n_panels_x-1)*left-0.01/n_panels_x,
                           bottom=bottom,
                           top=1-(n_panels_y-1)*bottom-0.1/n_panels_y,
                           wspace=0.18)

    for count, group_name in enumerate(group_names):
        pl.subplot(gs[count])
        gene_names = adata.uns[key]['names'][group_name]
        scores = adata.uns[key]['scores'][group_name]
        for ig, g in enumerate(gene_names[:n_genes]):
            gene_name = gene_names[ig]
            if adata.raw is not None and adata.uns[key]['params']['use_raw']:
                pl.text(
                    ig, scores[ig],
                    gene_name if gene_symbols is None else adata.raw.var[gene_symbols][gene_name],
                    rotation='vertical', verticalalignment='bottom',
                    horizontalalignment='center', fontsize=fontsize)
            else:
                pl.text(
                    ig, scores[ig],
                    gene_name if gene_symbols is None else adata.var[gene_symbols][gene_name],
                    rotation='vertical', verticalalignment='bottom',
                    horizontalalignment='center', fontsize=fontsize)
        pl.title('{} vs. {}'.format(group_name, reference))
        if count >= n_panels_x * (n_panels_y - 1): pl.xlabel('ranking')
        if count % n_panels_x == 0: pl.ylabel('score')
        ymin = np.min(scores)
        ymax = np.max(scores)
        ymax += 0.3*(ymax-ymin)
        pl.ylim([ymin, ymax])
        pl.xlim(-0.9, ig+1-0.1)
    writekey = ('rank_genes_groups_'
                + str(adata.uns[key]['params']['groupby']))
    utils.savefig_or_show(writekey, show=show, save=save)


@doc_params(show_save_ax=doc_show_save_ax)
def rank_genes_groups_violin(
        adata, groups=None, n_genes=20,
        gene_names=None, gene_symbols=None,
        use_raw=None,
        key=None,
        split=True,
        scale='width',
        strip=True, jitter=True, size=1,
        ax=None, show=None, save=None):
    """\
    Plot ranking of genes for all tested comparisons.

    Parameters
    ----------
    adata : :class:`~anndata.AnnData`
        Annotated data matrix.
    groups : list of `str`, optional (default: `None`)
        List of group names.
    n_genes : `int`, optional (default: 20)
        Number of genes to show. Is ignored if `gene_names` is passed.
    gene_names : `None` or list of `str` (default: `None`)
        List of genes to plot. Is only useful if interested in a custom gene list,
        which is not the result of :func:`scanpy.api.tl.rank_genes_groups`.
    gene_symbols : `str`, optional (default: `None`)
        Key for field in `.var` that stores gene symbols if you do not want to
        use `.var_names` displayed in the plot.
    use_raw : `bool`, optional (default: `None`)
        Use `raw` attribute of `adata` if present. Defaults to the value that
        was used in :func:`~scanpy.api.tl.rank_genes_groups`.
    split : `bool`, optional (default: `True`)
        Whether to split the violins or not.
    scale : `str`, optional (default: 'width')
        See `seaborn.violinplot`.
    strip : `bool`, optional (default: `True`)
        Show a strip plot on top of the violin plot.
    jitter : `int`, `float`, `bool`, optional (default: `True`)
        If set to 0, no points are drawn. See `seaborn.stripplot`.
    size : `int`, optional (default: 1)
        Size of the jitter points.
    {show_save_ax}
    """
    if key is None:
        key = 'rank_genes_groups'
    groups_key = str(adata.uns[key]['params']['groupby'])
    if use_raw is None:
        use_raw = bool(adata.uns[key]['params']['use_raw'])
    reference = str(adata.uns[key]['params']['reference'])
    groups_names = (adata.uns[key]['names'].dtype.names
                    if groups is None else groups)
    if isinstance(groups_names, str): groups_names = [groups_names]
    axs = []
    for group_name in groups_names:
        if gene_names is None:
            gene_names = adata.uns[
                key]['names'][group_name][:n_genes]
        df = pd.DataFrame()
        new_gene_names = []
        for g in gene_names:
            if adata.raw is not None and use_raw:
                X_col = adata.raw[:, g].X
            else:
                X_col = adata[:, g].X
            if issparse(X_col): X_col = X_col.toarray().flatten()
            new_gene_names.append(
                g if gene_symbols is None else adata.var[gene_symbols][g])
            df[g] = X_col
        df['hue'] = adata.obs[groups_key].astype(str).values
        if reference == 'rest':
            df.loc[df['hue'] != group_name, 'hue'] = 'rest'
        else:
            df.loc[~df['hue'].isin([group_name, reference]), 'hue'] = np.nan
        df['hue'] = df['hue'].astype('category')
        df_tidy = pd.melt(df, id_vars='hue', value_vars=new_gene_names)
        x = 'variable'
        y = 'value'
        hue_order = [group_name, reference]
        import seaborn as sns
        _ax = sns.violinplot(x=x, y=y, data=df_tidy, inner=None,
                             hue_order=hue_order, hue='hue', split=split,
                             scale=scale, orient='vertical', ax=ax)
        if strip:
            _ax = sns.stripplot(x=x, y=y, data=df_tidy,
                                hue='hue', dodge=True, hue_order=hue_order,
                                jitter=jitter, color='black', size=size, ax=_ax)
        _ax.set_xlabel('genes')
        _ax.set_title('{} vs. {}'.format(group_name, reference))
        _ax.legend_.remove()
        _ax.set_ylabel('expression')
        _ax.set_xticklabels(gene_names, rotation='vertical')
        writekey = ('rank_genes_groups_'
                    + str(adata.uns[key]['params']['groupby'])
                    + '_' + group_name)
        utils.savefig_or_show(writekey, show=show, save=save)
        axs.append(_ax)
    if show == False: return axs


def sim(adata, tmax_realization=None, as_heatmap=False, shuffle=False,
        show=None, save=None):
    """Plot results of simulation.

    Parameters
    ----------
    as_heatmap : bool (default: False)
        Plot the timeseries as heatmap.
    tmax_realization : int or None (default: False)
        Number of observations in one realization of the time series. The data matrix
        adata.X consists in concatenated realizations.
    shuffle : bool, optional (default: False)
        Shuffle the data.
    save : `bool` or `str`, optional (default: `None`)
        If `True` or a `str`, save the figure. A string is appended to the
        default filename. Infer the filetype if ending on {{'.pdf', '.png', '.svg'}}.
    show : bool, optional (default: `None`)
        Show the plot, do not return axis.
    """
    from ... import utils as sc_utils
    if tmax_realization is not None: tmax = tmax_realization
    elif 'tmax_write' in adata.uns: tmax = adata.uns['tmax_write']
    else: tmax = adata.n_obs
    n_realizations = adata.n_obs/tmax
    if not shuffle:
        if not as_heatmap:
            timeseries(adata.X,
                       var_names=adata.var_names,
                       xlim=[0, 1.25*adata.n_obs],
                       highlightsX=np.arange(tmax, n_realizations*tmax, tmax),
                       xlabel='realizations')
        else:
            # plot time series as heatmap, as in Haghverdi et al. (2016), Fig. 1d
            timeseries_as_heatmap(adata.X,
                                  var_names=adata.var_names,
                                  highlightsX=np.arange(tmax, n_realizations*tmax, tmax))
        pl.xticks(np.arange(0, n_realizations*tmax, tmax),
                  np.arange(n_realizations).astype(int) + 1)
        utils.savefig_or_show('sim', save=save, show=show)
    else:
        # shuffled data
        X = adata.X
        X, rows = sc_utils.subsample(X, seed=1)
        timeseries(X,
                   var_names=adata.var_names,
                   xlim=[0, 1.25*adata.n_obs],
                   highlightsX=np.arange(tmax, n_realizations*tmax, tmax),
                   xlabel='index (arbitrary order)')
        utils.savefig_or_show('sim_shuffled', save=save, show=show)
