python -m transformation_algebra vocab ^
    -L D:\repositories\cct\language.py ^
    -b marklogic -s https://qanda.soliscom.uu.nl:8000/

for %%v in (D:\repositories\cct\workflows\*.ttl) do ^
    python -m transformation_algebra graph ^
    -L D:\repositories\cct\language.py ^
    -T D:\repositories\cct\tools\tools.ttl ^
    -b marklogic -s https://qanda.soliscom.uu.nl:8000/ ^
    "%%v"
