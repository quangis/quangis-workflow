# quangis-workflows

As part of the [QuAnGIS](https://questionbasedanalysis.com/) project, 
this program can **synthesize** GIS workflows from a specification of 
GIS tools, using the [Automated Pipeline Explorer][ape]. It can also 
extract specifications of GIS tools from manually constructed workflows; 
as drawn from [this 
repository](https://github.com/quangis/QuAnGIS_workflow_annotation).


### Generation

There are two steps to the process: assembling a pipeline of tools, and 
annotating the conceptual steps they perform.

For the first step, datatypes and implementations are relevant. 
Therefore, the inputs and outputs of each tool in the 
[specification][tools] are annotated with core concept datatypes 
according to the [CCD][ccd] ontology. This is translated to a format 
that APE understands. APE is then instructed to generate workflows for 
different possible input/output data configurations. To perform this 
step, run:

    quangis-wf-gen

The second step involves abstracting away from implementation details. 
For this, the tools are also annotated with a description of their 
functionality by means of a [CCT][cct] expression. This information is 
weaved into a graph of conceptual transformations via the 
[`transforge`][tf] library. To perform this step, run the following on 
the generated workflows:

    transforge graph -L cct -T build/tools.ttl \
        --skip-error build/solution-*.ttl

Finally, to query tasks like those 
[here](https://github.com/quangis/cct/tree/master/tasks):

    transforge query -L cct tasks/*.ttl


### Dependencies

Java 1.8+ and Python 3.9+ must be installed, along with the dependencies 
in [`requirements.txt`](requirements.txt). The correct version of APE 
and other required data files will automatically be downloaded. To run 
(rather limited) tests, install and run `nose2`.


[ccd]: http://geographicknowledge.de/vocab/CoreConceptData.rdf
[jpype]: https://jpype.readthedocs.io/
[ape]: https://github.com/sanctuuary/APE
[aped]: https://ape-framework.readthedocs.io/
[cct]: https://github.com/quangis/cct
[tf]: https://github.com/quangis/transforge
[tools]: https://raw.githubusercontent.com/quangis/cct/master/tools/tools.ttl
[tools2]: https://github.com/simonscheider/QuAnGIS/tree/master/ToolRepository/ToolDescription.ttl
