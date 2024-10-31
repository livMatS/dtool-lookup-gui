## dtool datasets

A _dataset_ is a collection of files that belong together logically. For example, this could be...

* ...raw data recorded in a measurement.
* ...input files for a simulation and the output of that simulation.
* ...the LaTeX manuscript of a paper, the raw data underlying that paper and the scripts required to plot that data.

The idea behind a dataset is that it becomes immutable at some point. The process of making a dataset immutable is called 'freezing'. Once a dataset is frozen, it can be moved between storage systems but no longer be edited. Changing a dataset would then require the creation of a new (derived) dataset. While this may seem cumbersome, it has a few advantages: the storage backend can be kept simple, the inadvertent modification of primary data is not possible, and the data provenance is traceable exhaustively as long as derived datasets refer to their source datasets properly.

### Granularity

What goes into a _dataset_ is the decision of the dataset's creator. In general, a finer granularity makes it easier to move, copy and backup datasets. We distinguish between...

* ..._primary data_, i.e. the raw results from a measurement or the output of a simulation...
* ...and _secondary or derived data_, which is obtained by processing primary or other derived data. Derived data could for example be some elemental analysis based on some spectrometry measurement. The recorded spectrum itself would be primary data.

This distinction allows to freeze a dataset immediately after completion of an experiment, while there may still be many postprocessing steps that follow. Those would go into separate datasets. The relationship between datasets can be specified using the `derived_from` property or other means discussed below.

### Owners

Each dataset has at least one owner. This is typically the person who created the dataset. __Note that the owner has scientific responsibility for the contents of the dataset.__ Part of this scientific responsibility is for example ensuring that the data has not been fabricated or falsified. Attaching an owner to a dataset allows traceability of these scientific responsibilities.

## Metadata

A dataset _always_ has metadata attached to it. Common formats for specifying metadata of arbitrary complexity are [YAML](https://yaml.org/) and [JSON](https://www.json.org). *dtool* strongly ecourages the use of YAML. YAML is suitable for specifying metadata in simple key-value pairs, but can do much more. The [YAML cheatsheet](https://quickref.me/yaml) offers a compact overview on both formats. Often, metadata are categorized into administrative, bibliographic and descriptive metadata. The example below shows a minimum example of administrative metadata in YAML format. 

```yaml
project: 2023-11-09-dtool-example
description: Examples on how document a dtool dataset with YAML-formatted metadata 
owners:
  - name: Johannes Laurin Hoermann
    email: johannes.hoermann@imtek.uni-freiburg.de
    orcid: 0000-0001-5867-695X
funders:
  - organization: DFG
    program:  Clusters of Excellence
    code: EXC 2193
creation_date: '2023-11-09'
```

We recommend to always use your clear name, your email and your [ORCID](https://orcid.org/) for tracing ownership.
The more (descriptive) metadata are available, the easier it will be to search for a specific dataset.