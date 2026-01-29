from Wingman.core.controller import Controller

def test_InitializedModel_TriStateBooleanPropertiesSetToNone():
    c = Controller.ForTesting()
    
    assert c.model.isAfk is None
    assert c.model.isMeditating is None