The dtool story
===============

The dtool ecosystem is a collection of coupled open-source libraries and tools that support good research data management practices in a discipline-agnostic, decentralized manner.
At its core are the dtool_ command line interface and the dtoolcore_ Python API. They package data and their documentation into a self-contained whole, the *dataset*.
The authors have described their motivation and core ideas for condensing dtool concisely in

* T. S. G. Olsson and M. Hartley, “Lightweight data management with dtool,” PeerJ, vol. 7, p. e6562, Mar. 2019, doi: `10.7717/peerj.6562 <https://doi.org/10.7717/peerj.6562>`_.

Development took place during their time at the `John Innes Centre`_ and all code is maintained at `github.com/jic-dtool`_.

Around the time of this initial publication, the `simulation group`_ at the `Department of Microsystems Engineering`_ of the `University of Freiburg`_ picked up dtool as a lean and versatile solution for their internal data management.
Several aspects of using dtool in practice within this group has been summed up in the proceedings contribution

* J. L. Hörmann and L. Pastewka, “Lightweight research data management with dtool: a use case,” 2022, doi: `10.18725/OPARU-46062 <https://doi.org/10.18725/OPARU-46062>`_.

Together with the original authors of dtool, the Freiburg researchers continued to move the `dtool-lookup-server`_ project forward, a lean web server that makes collections of dtool datasets searchable.

For the ones looking at data under the aspects of findability, accessibility, interoperability, and reuse -- the `FAIR principles`_ -- the dtool-lookup-server introduces *findability* to dtool datasets.

As of 2023, dtool and the dtool-lookup-server have been of great support in compiling several PhD thesis and journal publications in Freiburg, e.g.

* A. Sanner and L. Pastewka, “Crack-front model for adhesion of soft elastic spheres with chemical heterogeneity,” Journal of the Mechanics and Physics of Solids, vol. 160, p. 104781, Mar. 2022, doi: `10.1016/j.jmps.2022.104781 <https://doi.org/10.1016/j.jmps.2022.104781>`_.
* J. L. Hörmann, C. (刘宸旭) Liu, Y. (孟永钢) Meng, and L. Pastewka, “Molecular simulations of sliding on SDS surfactant films,” The Journal of Chemical Physics, vol. 158, no. 24, p. 244703, Jun. 2023, doi: `10.1063/5.0153397 <https://doi.org/10.1063/5.0153397>`_.
* H. Holey, “Entwicklung einer Multiskalenmethode für die Simulation von Schmierprozessen,” Karlsruher Institut für Technologie (KIT), 2023. doi: `10.5445/IR/1000157008 <https://doi.org/10.5445/IR/1000157008>`_.

At Freiburg, dtool has been adapted as one component in the research data management (RDM) strategy of the `Cluster of Excellence livMatS`_.
Here it serves the twofold purpose of offering an independent fallback solution to improve their data management for any willing *liv*MatS affiliate not provided with RDM guidance elsewhere.
Secondly, dtool and the dtool-lookup-server provide a didactic bridge between the status quo of completely standard-free data management at the individual level at one end and fully FAIR platform solutions with rigid metadata documentation requirements at the other end.
This strategy has been outlined in a talk

* J. Hörmann, “livMatS Research Data Management Concept with a focus on the didactic use of dtool,” presented at the Data Stewardship Workshop 2022, Braunschweig, October 13th, 2022. doi: `<https://doi.org/10.24355/dbbs.084-202211091503-0>`_.

The dtool-lookup-gui serves as a graphical demonstrator for dtool and dtool-lookup-server functionality.
The aim of developing thi GUI is twofold as well.
Firstly, the GUI makes the dtool ecosystem accessible for users who do not work on the command line or via Python APIs.
Secondly, when used in RDM workshops together with an ephemeral dtool-lookup-server instance, it may illustrate a few core concepts of good data management with direct hands-on exercises, namely

* bundling data and documentation in a dataset
* treating data immutable
* attaching globally unique identifiers to datasets
* tracking provenance across many datasets
* the benefits of standardized metadata above free text documentation only when searching datasets
* the differences between administrative, bibliographic, and descriptive metadata

In one way or the other, these concepts underlie any other sophisticated data management framework. The dtool-lookup-gui however focuses on these ideas only and leaves any discipline-specific aspects aside, while encouraging the user to think about packaging granularity and the right degree of metadata standardization.

.. _dtoolcore: https://dtoolcore.readthedocs.io/en/latest
.. _dtool: https://dtool.readthedocs.io/en/latest/
.. _github.com/jic-dtool: https://github.com/jic-dtool/
.. _John Innes Centre: https://www.jic.ac.uk/
.. _simulation group: https://pastewka.org/
.. _Department of Microsystems Engineering: https://imtek.uni-freiburg.de
.. _University of Freiburg: https://uni-freiburg.de/en/
.. _dtool-lookup-server: https://github.com/jic-dtool/dtool-lookup-server
.. _Cluster of Excellence livMatS: https://www.livmats.uni-freiburg.de
.. _FAIR principles: https://www.go-fair.org/fair-principles/