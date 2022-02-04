import drfs



TestModel = drfs.generate_model('TestModel.json')
TestModel2 = drfs.generate_model('TestModel2.json')

TestModelWithOwner = drfs.generate_model('TestModelWithOwner.json')

ModelWithRefToTestModel = drfs.generate_model('ModelWithRefToTestModel.json')
TestModelWithRelations_Flat = drfs.generate_model('TestModelWithRelations_Flat.json')
TestModelWithRelations_Nested = drfs.generate_model('TestModelWithRelations_Nested.json')
TestModelRalationBelongsTo = drfs.generate_model('TestModelRalationBelongsTo.json')
TestModelRalationBelongsTo_withIgnore404Object = drfs.generate_model('TestModelRalationBelongsTo_withIgnore404Object.json')
TestModelRalationHasOne = drfs.generate_model('TestModelRalationHasOne.json')


TestModelAbstract = drfs.generate_model('TestModelAbstract.json')
TestModelForJsonData = drfs.generate_model('TestModelForJsonData.json')


TestModelWithEmbeddedOne = drfs.generate_model('TestModelWithEmbeddedOne.json')
TestModelWithEmbeddedManyAsObject = drfs.generate_model('TestModelWithEmbeddedManyAsObject.json')
