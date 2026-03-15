import pytest
from Wingman.core.resource_bar import ResourceBar

class TestResourceBar:

    def test_Initialization(self):
        rb = ResourceBar(current=50, maximum=100)
        assert rb.Current == 50
        assert rb.Maximum == 100
    
    def test_MakingIntoString(self):
        rb = ResourceBar(current=75, maximum=150)
        assert str(rb) == "75/150"

    def test_Equality_SameValues_FromDifferentInstances_Passes(self):
        rb1 = ResourceBar(current=30, maximum=60)
        rb2 = ResourceBar(current=30, maximum=60)

        assert rb1 == rb2
    
    def test_Inequality_DifferentValues_FromDifferentInstances_Fails(self):
        rb1 = ResourceBar(current=30, maximum=61)
        rb2 = ResourceBar(current=31, maximum=60)

        assert rb1 != rb2
    
    @pytest.mark.parametrize("input,expected", argvalues=[
                                                ("75/150", ResourceBar(75, 150)),
                                                ("75/ 150", ResourceBar(75, 150))
                                                ], 
                                                ids=[
                                                    "NoSpaceBeforeMaximum",
                                                    "WithSpacesBeforeMaximum"
                                                    ]
    )
    def test_Initialization_FromString(self, input: str, expected: ResourceBar):
        rb = ResourceBar.FromString(input)

        assert rb == expected
    
    @pytest.mark.parametrize("input,stringRepresentation", argvalues=[
                                                            (ResourceBar(100, 100), "100/100"),
                                                            (ResourceBar(100, 100), "100/ 100")
                                                            ],
                                                            ids=[
                                                                "NoSpaceBeforeMaximum",
                                                                "WithSpaceBeforeMaximum"
                                                            ]
    )
    def test_Equality_ResourceBarAndStringRepresentation(self, input: ResourceBar, stringRepresentation: str):
        assert input == stringRepresentation

    def test_CurrentWithNonDigitCharacter_RaisesValueError(self):
        with pytest.raises(ValueError):
            ResourceBar.FromString("7a/150")

    def test_MaximumWithNonDigitCharacter_RaisesValueError(self):
        with pytest.raises(ValueError):
            ResourceBar.FromString("75/1b0")
