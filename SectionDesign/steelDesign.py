
class SteelSectionDesign:
    def __init__(self, section):
        self.sectionProperties = None
        pass

    # This function return Shape, Area, t3, t2, tf, tw, r33, r22, I33, I22, S33Top, S22Left, Z33, Z22
    def getProp(self, section, property):
        # Get the section properties from the dictionary, using the section name
        # as the key
        return self.sectionProperties[section][property]
    
    def getDesignLoad(self, frameID, loadCase):
        return self.designLoad[frameID][loadCase]


    
