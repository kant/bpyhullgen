# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

import bpy 
import math
from math import radians, degrees
import bmesh

from ..hullgen import curve_helper
from ..hullgen import material_helper
from ..hullgen import curve_helper
from ..hullgen import chine_helper
from ..hullgen import bulkhead
from ..hullgen import keel_helper
from ..hullgen import geometry_helper
from ..hullgen import bpy_helper
from bpyhullgen.hullgen import prop_helper

class hull_maker:
	hull_length=11.4
	hull_width=3.9
	hull_height=3.6

	make_bulkheads=True
	make_keels=True
	make_longitudals=True
	hide_hull=True
		
	default_floor_height=-0.7

	hull_name="hull_object"
	cleaner_collection_name="cleaner"

	hull_object=None

	curve_resolution=24
	
	chine_list=None

	# this will be inherited by members
	structural_thickness=0.06

	bulkhead_instances=None
	keel_list=None
	props=None

	bulkhead_definitions=None

	# Objects that are subtracted from hull to modify final shape
	subtractive_objects=None


	# longitudal spacing is based on bulkheads
	bulkhead_spacing=1.0

	start_bulkhead_location=-3
	bulkhead_count=6
	bulkhead_thickness=0.05

	# output scale for fabrication = 1:16 = 1/16 = 0.0625
	hull_output_scale=1

	# screw size in MM
	target_screw_size=10 # target size in output model

	
	def clear_all(self):

		# A temporary list of things to delete
		delete_list=[]

		if self.hull_object != None:
			delete_list.append(self.hull_object)


		for bh in self.bulkhead_instances:
			delete_list.append(bh.bulkhead_void_object)
			delete_list.append(bh.bulkhead_object)

		for chine in self.chine_list:
			for chine_instance in chine.chine_instances:

				delete_list.append(chine_instance.curve_object)
				delete_list.append(chine_instance.curve_backup)
				
				for lg in chine_instance.longitudal_slicers:
					delete_list.append(lg)

				for lg in chine_instance.longitudal_objects:
					delete_list.append(lg)

		for keel in self.keel_list:
			delete_list.append(keel.keel_slicer_object)
			delete_list.append(keel.keel_object)

		
		if len(delete_list) > 0:
			#print("Delete:%s"%delete_list)
			bpy.ops.object.select_all(action='DESELECT')

			objs = bpy.data.objects

			for ob in delete_list:
				objs.remove(ob, do_unlink=True)

		self.hull_object=None

		self.keel_list.clear()
		self.bulkhead_definitions.clear()
		self.chine_list.clear()
		self.props.clear()
		self.bulkhead_instances.clear()
		self.subtractive_objects.clear()
	


	def __init__(self,length=11.4,width=3.9,height=3.6):

		self.keel_list=[]
		self.bulkhead_definitions=[]
		self.chine_list=[]
		self.props=[]
		self.bulkhead_instances=[]
		self.subtractive_objects=[]


		self.hull_height=height
		self.hull_length=length
		self.hull_width=width

	def add_chine(self,new_chine):
		self.chine_list.append(new_chine)

	def add_subtractive_object(self,object):
		self.subtractive_objects.append(object)


	def make_hull_object(self):
		self.hull_object=geometry_helper.make_cube(self.hull_name,size=(self.hull_length, self.hull_width, self.hull_height))

		material_helper.assign_material(self.hull_object,material_helper.get_material_hull())

		view_collection_hull=bpy_helper.make_collection("hull",bpy.context.scene.collection.children)
		bpy_helper.move_object_to_collection(view_collection_hull,self.hull_object)


		return self.hull_object

	def add_bulkhead_definition(self,bulkhead_definition):
		self.bulkhead_definitions.append(bulkhead_definition)


	def add_auto_bulkheads(self):

		current_bulkhead_location=self.start_bulkhead_location
		for bulkhead_index in range(0,self.bulkhead_count):
			watertight=False
			floor_height=self.default_floor_height

			new_bulkhead_definition=bulkhead.bulkhead_definition(
				station=current_bulkhead_location,
				watertight=watertight,
				floor_height=floor_height,
				thickness=self.bulkhead_thickness
			)

			self.add_bulkhead_definition(new_bulkhead_definition)
			current_bulkhead_location+=self.bulkhead_spacing
			#print("add bulkhead %d station: %f watertight: %d floor: %f"%(bulkhead_index,current_bulkhead_location,watertight,floor_height))


	def make_bulkhead_objects(self,bulkhead_definitions):

		for bulkhead_definition in self.bulkhead_definitions:

			bh=bulkhead.bulkhead(self,bulkhead_definition)
								
			bh.make_bulkhead()

			# If it's not watertight - there is a void in middle
			if bulkhead_definition.watertight==False:
				material_helper.assign_material(bh.bulkhead_void_object,material_helper.get_material_bool())
				
				floor_height_z=bulkhead_definition.floor_height

				# floor height
				if floor_height_z!=False:

					floor_bool_name="floor_bool_%s"%floor_height_z

					ob = bpy.data.objects.get(floor_bool_name)

					if ob is None:
						ob = geometry_helper.make_cube(name=floor_bool_name,
							location=[0,0,0],
							size=[self.hull_length,self.hull_width,self.hull_height])

						ob.location.z=0-(self.hull_height/2)+floor_height_z
						ob.hide_viewport=True
						ob.hide_render=True

						view_collection_cleaner=bpy_helper.make_collection(self.cleaner_collection_name,bpy.context.scene.collection.children)
						bpy_helper.move_object_to_collection(view_collection_cleaner,ob)

						
					modifier=bh.bulkhead_void_object.modifiers.new(name="floor", type='BOOLEAN')
					modifier.object=ob
					modifier.operation="DIFFERENCE"

		
			self.bulkhead_instances.append(bh)

			material_helper.assign_material(bh.bulkhead_object,material_helper.get_material_bulkhead())

			if bh.bulkhead_void_object!=None:
				bpy_helper.select_object(bh.bulkhead_void_object,True)
			
				bpy_helper.bmesh_recalculate_normals(bh.bulkhead_void_object)
				
				bpy_helper.hide_object(bh.bulkhead_void_object)
			
			bpy_helper.parent_objects_keep_transform(parent=self.hull_object,child=bh.bulkhead_object)

			bh.bulkhead_object.parent=self.hull_object


	def add_prop(self, rotation=None,
						location=None,
						blend_file="props.blend",
						library_path="Collection",
						target_object="myprop",
						parent=None):
		# this is a bit redundant - passing all the parameters through like this
		# but it allows us to make one call add_prop without having to make the object
		# then add to the hull from the external caller
		new_prop=prop_helper.prop_helper(blend_file=blend_file,
			rotation=rotation, location=location,
			library_path=library_path,
			target_object=target_object,
			parent=parent)
		
		self.props.append(new_prop)

	def integrate_props(self):
		view_collection_props=bpy_helper.make_collection("props",bpy.context.scene.collection.children)

		for prop in self.props:
			ob=prop.import_object(view_collection_props)
			bpy_helper.move_object_to_collection(view_collection_props,ob)

	def integrate_components(self):
		# The order of boolean operations is important... If order not organized correctly strange things happen

		print("Integrate")

		performance_timer = bpy_helper.ElapsedTimer()


		hide_hull=False
		use_subtractive_objects=False
		use_props=False

		#======================================
		# Single configuration area for generation overrides
		#======================================
		use_subtractive_objects=True
		use_props=True
		#======================================
		
		# Longitudal stringers created at same time as chines so as to reuse the curve
		for chine_object in self.chine_list:
				chine_object.longitudal_elements_enabled=self.make_longitudals
				chine_object.make_chine()


		self.make_chine_hull_booleans()				

		if self.make_keels:
			for keel in self.keel_list:
				keel.make_keel()

		if self.make_bulkheads:
			#self.add_auto_bulkheads()
			self.make_bulkhead_objects(self.bulkhead_definitions)			

		if use_props:
			self.integrate_props()	

		if self.make_keels:
			self.make_keel_booleans()

		if self.make_bulkheads:
			self.make_bulkhead_booleans()

		if self.make_longitudals:
			self.make_longitudal_booleans()

		if use_subtractive_objects:
			self.apply_subtractive_objects()

		if self.hide_hull:
			self.hull_object.hide_viewport=True

		performance_timer.get_elapsed_string()

	def add_keel(self,keel):
		self.keel_list.append(keel)

	def apply_subtractive_objects(self):

		for ob in self.subtractive_objects:

			ob.hide_render=True
			ob.hide_viewport=True
			ob.display_type="WIRE"

			bool_name="subtract_%s"%ob.name
			bool_new = self.hull_object.modifiers.new(type="BOOLEAN", name=bool_name)
			bool_new.object = ob
			bool_new.operation = 'DIFFERENCE'

			for chine in self.chine_list:
				for chine_instance in chine.chine_instances:
					for lg in chine_instance.longitudal_objects:				
						if geometry_helper.check_intersect(ob,lg):
							modifier=lg.modifiers.new(type='BOOLEAN',name=bool_name)
							modifier.object=ob
							modifier.operation="DIFFERENCE"


	def make_bulkhead_booleans(self):
	
		for bh in self.bulkhead_instances:
			bool_void = bh.bulkhead_object.modifiers.new(type="BOOLEAN", name="void.center_%d"%bh.bulkhead_definition.station)
			bool_void.object = bh.bulkhead_void_object
			bool_void.operation = 'DIFFERENCE'


	def make_longitudal_booleans(self):

		for chine in self.chine_list:
			for chine_instance in chine.chine_instances:

				
				
				for lg in chine_instance.longitudal_slicers:

					for bh in self.bulkhead_instances:
						#print("bh: %s"%bh.bulkhead_object.name,end=" ")
						# TODO for some reason interection code not returning correct result
						if geometry_helper.check_intersect(bh.bulkhead_object,lg) or True:
							modifier=bh.bulkhead_object.modifiers.new(name=lg.name, type='BOOLEAN')
							modifier.object=lg
							modifier.operation="DIFFERENCE"

				for lg in chine_instance.longitudal_objects:
						for bh in self.bulkhead_instances:
							# TODO for some reason interection code not returning correct result
							if geometry_helper.check_intersect(bh.bulkhead_object,lg) or True:
								modifier=lg.modifiers.new(name=bh.bulkhead_object.name, type='BOOLEAN')
								modifier.object=bh.bulkhead_object
								modifier.operation="DIFFERENCE"



	def make_longitudal_elements(self):
		for chine_object in self.chine_list:
			chine_object.make_longitudal_elements()

	def make_chine_hull_booleans(self):

		for chine_object in self.chine_list:	
			for chine_instance in chine_object.chine_instances:		
				slicename="slice.%s"%chine_instance.curve_object.name

				bool_new = self.hull_object.modifiers.new(type="BOOLEAN", name=slicename)
				bool_new.object = chine_instance.curve_object
				bool_new.operation = 'DIFFERENCE'


	def make_keel_booleans(self):

		for keel in self.keel_list:

			for bh in self.bulkhead_instances:

				if geometry_helper.check_intersect(bh.bulkhead_object,keel.keel_slicer_object):

					# notch the bulkhead with keel_slicer_object
					modifier_name="%s_%s"%(bh.bulkhead_object.name,keel.keel_slicer_object.name)
					modifier=bh.bulkhead_object.modifiers.new(name=modifier_name, type='BOOLEAN')
					modifier.object=keel.keel_slicer_object
					modifier.operation="DIFFERENCE"

					bpy_helper.select_object(bh.bulkhead_object,True)
  

					# notch the keel with modified bulkhead 
					modifier_name="%s_%s"%(bh.bulkhead_object.name,keel.keel_object.name)
					modifier=keel.keel_object.modifiers.new(name=modifier_name, type='BOOLEAN')
					modifier.object=bh.bulkhead_object
					modifier.operation="DIFFERENCE"

			bpy_helper.select_object(keel.keel_object,True)

			material_helper.assign_material(keel.keel_object,material_helper.get_material_keel())

			keel.keel_object.parent=self.hull_object


	# Cleans up longitudal framing in center of hull for access to entrance / pilothouse 
	# so longitudal frames don't block entrance
	def cleanup_center(self,clean_location,clean_size):

		view_collection_cleaner=bpy_helper.make_collection(self.cleaner_collection_name,bpy.context.scene.collection.children)

		object_end_clean = geometry_helper.make_cube("mid_clean_%s"%clean_location[0],location=clean_location,size=clean_size)

		bpy_helper.move_object_to_collection(view_collection_cleaner,object_end_clean)

		material_helper.assign_material(object_end_clean,material_helper.get_material_bool())

		for lg in self.longitudal_list:

			modifier=lg.modifiers.new(name="bool", type='BOOLEAN')
			modifier.object=object_end_clean
			modifier.operation="DIFFERENCE"
			bpy_helper.hide_object(object_end_clean)

	# Trims the ends of the longitudal framing where it extends past last bulkhead
	# x_locations is a list of stations where they will be chopped
	# rotations is a corresponding list of rotations in the Y axis. Bulkheads are assumed to be not rotated on X an Z axises. 
	def cleanup_longitudal_ends(self,x_locations,rotations=None):

		view_collection_cleaner=bpy_helper.make_collection(self.cleaner_collection_name,bpy.context.scene.collection.children)

		end_clean_list=[]

		for index,x_location in enumerate(x_locations):
			# =========================================
			# Clean up ends of longitudal slicers

			block_width=self.hull_width

			adjusted_location=x_location
			if adjusted_location<0:
				adjusted_location=adjusted_location-block_width/2

			if adjusted_location>0:
				adjusted_location=adjusted_location+block_width/2

			object_end_clean = geometry_helper.make_cube("end_clean_%s"%index,location=[adjusted_location,0,0],size=(block_width,block_width,self.hull_height))

			if rotations!=None:
				bpy_helper.select_object(object_end_clean,True)
				bpy.ops.transform.rotate(value=radians(rotations[index]),orient_axis='Y')

			bpy_helper.move_object_to_collection(view_collection_cleaner,object_end_clean)

			material_helper.assign_material(object_end_clean,material_helper.get_material_bool())
			end_clean_list.append(object_end_clean)

		# ===================================================================

			for chine_object in self.chine_list:	
				for chine_instance in chine_object.chine_instances:	
					#print("chine: %s"%chine_instance)
					for lg in chine_instance.longitudal_objects:
						#print("eval: %s"%lg.name)
						for object_end_clean in end_clean_list:
							#print("clean: %s"%object_end_clean.name)
							if geometry_helper.check_intersect(lg,object_end_clean):
								modifier=lg.modifiers.new(name="bool", type='BOOLEAN')
								modifier.object=object_end_clean
								modifier.operation="DIFFERENCE"
								bpy_helper.hide_object(object_end_clean)

		bpy_helper.hide_object(view_collection_cleaner)
