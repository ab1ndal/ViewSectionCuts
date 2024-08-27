# Create a class that takes in two classes and converts the units of the first type to the units of the second type
# The class should have functions that takes the input value in the first type and he type of input value like force, moment, etc and returns the value in the second type

class UnitConvertor:
    def __init__(self, unitTypeIn, unitTypeOut):
        self.InForce, self.InLen, self.InTemp = unitTypeIn.split(',')
        self.OutForce, self.OutLen, self.OutTemp = unitTypeOut.split(',')
        self.LenFactor = self.convert_length(1)
        self.ForceFactor = self.convert_force(1)

    def convert_length(self, value):
        # Conversion factors relative to meters
        conversion_factors = {
        'in': 0.0254,  # inches to meters
        'ft': 0.3048,  # feet to meters
        'mm': 0.001,   # millimeters to meters
        'm': 1.0,      # meters to meters
        'cm': 0.01     # centimeters to meters
        }
        
        # Convert from the original unit to meters
        value_in_meters = value * conversion_factors[self.InLen]

        # Convert from meters to the desired unit
        converted_value = value_in_meters / conversion_factors[self.OutLen]

        return converted_value
    
    def convert_force(self, value):
        #Conversion between lb,kip,N,kN,Kgf,Tonf
        conversion_factors = {
        'lb': 4.44822,  # pounds to newtons
        'kip': 4448.22, # kips to newtons
        'N': 1.0,       # newtons to newtons
        'kN': 1000.0,   # kilonewtons to newtons
        'Kgf': 9.80665, # kilogram-force to newtons
        'Tonf': 9806.65 # ton-force to newtons
        }

        # Convert from the original unit to newtons
        value_in_newtons = value * conversion_factors[self.InForce]

        # Convert from newtons to the desired unit
        converted_value = value_in_newtons / conversion_factors[self.OutForce]
        
        return converted_value
    
    def convert_temperature(self, value):
        #Conversion between F and C
        if self.InTemp == 'F' and self.OutTemp == 'C':
            return (value - 32) * 5/9
        elif self.InTemp == 'C' and self.OutTemp == 'F':
            return (value * 9/5) + 32
        else:
            return value
        
    def convert(self, value, valueType):
        if valueType == 'force':
            return self.convert_force(value)
        elif valueType == 'length':
            return self.convert_length(value)
        elif valueType == 'temperature':
            return self.convert_temperature(value)
        elif valueType == 'moment':
            return value * self.ForceFactor * self.LenFactor
        else:
            raise ValueError(f'Invalid valueType: {valueType}')
    
    def printUnit(self, valueType):
        if valueType == 'force':
            return self.OutForce
        elif valueType == 'length':
            return self.OutLen
        elif valueType == 'temperature':
            return self.OutTemp
        elif valueType == 'moment':
            return self.OutForce + '-' + self.OutLen
        else:
            raise ValueError(f'Invalid valueType: {valueType}')

