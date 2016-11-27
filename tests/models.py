import drfs



TestModel = drfs.generate_model('TestModel.json')
TestModel2 = drfs.generate_model('TestModel2.json')

TestModelWithOwner = drfs.generate_model('TestModelWithOwner.json')

ModelWithRefToTestModel = drfs.generate_model('ModelWithRefToTestModel.json')
