import pandas as pd
from utils.readFile import *
import plotly.graph_objects as go

class StructuralPlotter:
    def __init__(self, joints_df, frames_df, areas_df, groups_df):
        self.joints_df = joints_df
        self.frames_df = frames_df
        self.areas_df = areas_df
        self.groups_df = groups_df
        self.assign_colors(joint_color='lightgrey', frame_color='lightgrey', area_color='lightgrey', highlighted_color='red')
        print('StructuralPlotter initialized')

    def assign_colors(self, joint_color, frame_color, area_color, highlighted_color):
        """Assign colors to components and highlighted components."""
        self.joint_color = joint_color
        self.frame_color = frame_color
        self.area_color = area_color
        self.highlight_color = highlighted_color

    def plot_components(self, component_type, highlighted_labels=None):
        """Plot joints, frames, or areas in 3D space, highlighting specified components if provided."""
        traces = []
        
        # Common method to create a trace for highlighted components
        def create_highlight_trace(data, color, name, marker_size=6):
            return go.Scatter3d(
                x=data['X'],
                y=data['Y'],
                z=data['Z'],
                mode='markers',
                marker=dict(size=marker_size, color=color, opacity=1.0),
                name=name
            )

        if component_type == 'Joint':
            # Plot all joints
            traces.append(create_highlight_trace(self.joints_df, self.joint_color, 'Joints', marker_size=3))

            # Highlight specified joints
            if highlighted_labels is not None:
                highlighted_joints = self.joints_df[self.joints_df['JointLabel'].isin(highlighted_labels)]
                if not highlighted_joints.empty:
                    traces.append(create_highlight_trace(highlighted_joints, self.highlight_color, 'Highlighted Joints'))

        elif component_type == 'Frame':
            for _, row in self.frames_df.iterrows():
                joint_i = self.joints_df[self.joints_df['JointLabel'] == row['JointILabel']].iloc[0]
                joint_j = self.joints_df[self.joints_df['JointLabel'] == row['JointJLabel']].iloc[0]
                color = self.highlight_color if highlighted_labels and row['FrameLabel'] in highlighted_labels else self.frame_color
                width = 4 if highlighted_labels and row['FrameLabel'] in highlighted_labels else 2
                traces.append(go.Scatter3d(
                    x=[joint_i['X'], joint_j['X']],
                    y=[joint_i['Y'], joint_j['Y']],
                    z=[joint_i['Z'], joint_j['Z']],
                    mode='lines',
                    line=dict(color=color, width=width),
                    name='Highlighted Frames' if highlighted_labels else 'Frames'
                ))

        elif component_type == 'Area':
            for _, row in self.areas_df.iterrows():
                joint_list = row['JointList']
                area_joints_df = self.joints_df[self.joints_df['JointLabel'].isin(joint_list)]
                color = self.highlight_color if highlighted_labels and row['AreaLabel'] in highlighted_labels else self.area_color
                traces.append(go.Mesh3d(
                    x=area_joints_df['X'],
                    y=area_joints_df['Y'],
                    z=area_joints_df['Z'],
                    color=color,
                    opacity=0.5,
                    name='Highlighted Areas' if highlighted_labels else 'Areas'
                ))
        
        return traces


    def highlight_components(self, component_type, labels):
        """Highlight specified components based on type (Joint, Frame, or Area)."""
        return self.plot_components(component_type, highlighted_labels=labels)

    def highlight_group(self, group_label):
        """Highlight all components (Joints, Frames, Areas) in the specified group."""
        highlight_traces = []
        
        # Filter the group by GroupLabel
        highlighted_df = self.groups_df[self.groups_df['GroupLabel'] == group_label]
        
        for component_type in highlighted_df['ComponentType'].unique():
            component_labels = highlighted_df[highlighted_df['ComponentType'] == component_type]['ComponentLabel'].tolist()
            highlight_traces.extend(self.highlight_components(component_type, component_labels))
        
        return highlight_traces

    def show_plot(self, group_label=None):
        """Show the 3D plot, highlighting the specified group if provided."""
        traces = self.plot_components('Joint') + self.plot_components('Frame') + self.plot_components('Area')
        
        if group_label:
            traces += self.highlight_group(group_label)

        layout = go.Layout(
            scene=dict(
                xaxis=dict(showgrid=False, zeroline=False, visible=False),
                yaxis=dict(showgrid=False, zeroline=False, visible=False),
                zaxis=dict(showgrid=False, zeroline=False, visible=False)
            ),
            showlegend=False,
            margin=dict(r=10, l=10, b=10, t=10)
        )

        fig = go.Figure(data=traces, layout=layout)
        fig.show()

class readData:
    def __init__(self, filePath):
        self.filePath = filePath
        self.connection = self.getConnection(self.filePath)

    def getConnection(self, file):
        data = connectDB(file, 'Geometry')
        # Iterate through the generator to capture progress updates
        for update in data:
            if isinstance(update, dict) and 'progress' in update:
                print(update['message'])  # Handle progress reporting
            else:
                conn = update  # The connection will be yielded last
                break
        return conn
    
    def getJointCoord(self):
        jointCoord = getData(self.connection, query='SELECT "Joint" AS "JointLabel", CAST("GlobalX" as NUMERIC) as "X", CAST("GlobalY" as NUMERIC) as "Y", CAST("GlobalZ" as NUMERIC) as "Z" FROM "Joint Coordinates"')
        return jointCoord
    
    def getFrames(self):
        frames = getData(self.connection, query='SELECT "Frame" AS "FrameLabel", "JointI" AS "JointILabel", "JointJ" AS "JointJLabel" FROM "Connectivity - Frame"')
        return frames
    
    def getAreas(self):
        # I have NumJoints, Joint1, Joint2, Joint3, Joint4
        # I need to convert this to JointList
        # If we have more than 4 joints, read the next line.

        query = '''
        SELECT "Area" AS "AreaLabel",
        ARRAY["Joint1", "Joint2", "Joint3", "Joint4"] AS "JointList"
        FROM "Connectivity - Area"
        '''

        areas = getData(self.connection, query=query)
        return areas
    
    def getGroups(self):
        groups = getData(self.connection, query='SELECT "GroupName" AS "GroupLabel", "ObjectType" as "ComponentType", "ObjectLabel" AS "ComponentLabel" FROM "Groups 2 - Assignments"')
        return groups


if __name__ == '__main__':
    filePath = r"C:\\Users\\abindal\\OneDrive - Nabih Youssef & Associates\\Documents\\00_Projects\\06_The Vault\\302_Geometry.xlsx"
    newModel = readData(filePath)
    joints = newModel.getJointCoord()
    frames = newModel.getFrames()
    areas = newModel.getAreas()
    groups = newModel.getGroups()

    # Create a plotter instance
    plotter = StructuralPlotter(joints[:1000], frames[:100], areas[:100], groups)

    # Show the plot, highlighting group 'G1'
    plotter.show_plot(group_label='Core3Conc')


# Sample DataFrames for demonstration
joints_df = pd.DataFrame({
    'JointLabel': ['J1', 'J2', 'J3'],
    'X': [0, 1, 2],
    'Y': [0, 1, 0],
    'Z': [0, 0, 1]
})

frames_df = pd.DataFrame({
    'FrameLabel': ['F1', 'F2'],
    'JointILabel': ['J1', 'J2'],
    'JointJLabel': ['J2', 'J3']
})

areas_df = pd.DataFrame({
    'AreaLabel': ['A1'],
    'JointList': [['J1', 'J2', 'J3']]
})

groups_df = pd.DataFrame({
    'GroupLabel': ['G1', 'G1', 'G1', 'G2'],
    'ComponentType': ['Joint', 'Frame', 'Area', 'Joint'],
    'ComponentLabel': ['J2', 'F1', 'A1','J1']
})

# Create a plotter instance
plotter = StructuralPlotter(joints_df, frames_df, areas_df, groups_df)

# Show the plot, highlighting group 'G1'
plotter.show_plot(group_label='G1')
