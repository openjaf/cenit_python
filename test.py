from cenit import api
from cenit import models


if __name__ == '__main__':
    api.register_custom_cenit(host='localhost', port=3000, ssl=False)
    api.use_credentials('N733085915', '3BxW5HDQyBYSxNZsqq7X')

    # library = definitions.Library("Test Library")
    # if library.push():
    #     print "<Library[%s]: %s>" % (library.id, library.name)
    # TODO: library.drop()

    libs = models.Library.fetch(slug="test_library")
    # tlib = libs and libs[0] or None

    # schema = definitions.Schema(tlib, "Test2.json", '{"type": "object"}')
    # if schema.push():
    #     print schema

    # sch_dt = models.SchemaDataType(tlib, "Schema DT 2", '{"type": "object"}')
    # if sch_dt.push():
    #     print sch_dt

    for lib in libs:
        print lib
        print "\t", lib.schemas
        print "\t", lib.data_types
        print

    # events = models.Observer.fetch()
    # for obs in events:
    #     print obs
