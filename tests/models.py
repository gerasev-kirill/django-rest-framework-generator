import drfs



TestModel = drfs.generate_model('TestModel.json')
TestModel2 = drfs.generate_model('TestModel2.json')

TestModelWithOwner = drfs.generate_model('TestModelWithOwner.json')

ModelWithRefToTestModel = drfs.generate_model('ModelWithRefToTestModel.json')

TestModelL10nFile = drfs.generate_model('TestModelL10nFile.json')
TestModelL10nFileList = drfs.generate_model('TestModelL10nFileList.json')
