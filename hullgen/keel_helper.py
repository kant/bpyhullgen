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

from math import radians

from ..hullgen import curve_helper
from ..hullgen import bpy_helper

class keel:
	lateral_offset=0
	top_height=0
	the_hull=None
	thickness=0.1
	keel_object=None
	view_keel_collection=None

	# measured in Longitudal station (X position) 
	station_start=0
	station_end=1

	#limit_x_min=0
	#limit_x_max=0

	
	slicer_cut_height=0.2

	keel_slicer_object=None
	keel_slicer_collection=None

	def __init__(self,the_hull,lateral_offset,top_height,station_start,station_end):
		self.lateral_offset=lateral_offset
		self.top_height=top_height
		self.the_hull=the_hull
		self.view_keel_collection=bpy_helper.make_collection("keels",bpy.context.scene.collection.children)
		self.station_start=station_start
		self.station_end=station_end

		#self.thickness=the_hull.structural_thickness

		#bpy_helper.hide_object(self.bulkhead_void_collection)

	#def set_limit_x_length(self,min,max):
	#	self.limit_x_max=max
	#	self.limit_x_min=min


	def make_keel_object(self,name,top_height_offset):

		cube_size=1.0
		
		keel_length=self.station_end-self.station_start

		# =====================================================
		# Make Keel Slicer for notches
		# =====================================================
		bpy.ops.mesh.primitive_cube_add(size=cube_size, 
			enter_editmode=False, 
			location=(  self.station_start+keel_length/2, 
						self.lateral_offset, 
						self.top_height))
		

		bpy.ops.transform.resize(value=(keel_length, 
								self.thickness, 
								self.the_hull.hull_height))

		bpy.ops.transform.translate(value=(0,0,-self.the_hull.hull_height/2-(top_height_offset)))

		bpy.ops.object.transform_apply(scale=True,location=False)
		
		new_object=bpy.context.view_layer.objects.active
		new_object.name="%s.s%0.2f"%(name,self.lateral_offset)

		

		bpy_helper.select_object(new_object,True)
		bpy_helper.move_object_to_collection(self.view_keel_collection,new_object)


		bool_new = new_object.modifiers.new(type="BOOLEAN", name="bool.hull_shape")
		bool_new.object = self.the_hull.hull_object
		bool_new.operation = 'INTERSECT'

		bpy_helper.select_object(new_object,True)
		#bpy.ops.object.modifier_apply(modifier=bool_new.name)

		bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

		return new_object



	def make_keel(self,slicer_cut_height=0.2):

		self.slicer_cut_height=slicer_cut_height

		self.keel_slicer_object=self.make_keel_object("Keel_Slicer",slicer_cut_height)
		self.keel_slicer_object.display_type="WIRE"
		self.keel_slicer_object.hide_render = True
		self.keel_slicer_object.hide_viewport = True

		self.keel_object=self.make_keel_object("Keel",0)
		#self.keel_slicer_object.display_type="WIRE"
		#self.keel_slicer_object.hide_render = True

		return self.keel_object
			

	def make_keel_old(self,slicer_cut_height=0.2):
		cube_size=1.0
		self.slicer_cut_height=slicer_cut_height

		thickness_shift=0

		# we always want to solidify from outside to inside
		# because we use a plane so we can get square edges on bottom where it meets hull 
		# to mimic plate material

		if self.lateral_offset>0:
			thickness_shift=-self.thickness
		else:
			thickness_shift=self.thickness


		bpy.ops.mesh.primitive_plane_add(size=cube_size, 
			enter_editmode=False, 
			location=(  self.station_start+keel_length/2, 
						self.lateral_offset-thickness_shift/2, 
						self.top_height))

		#bpy.ops.mesh.primitive_cube_add(size=cube_size, 
		#    enter_editmode=False, 
		#    location=(  0, self.lateral_offset, self.top_height))
		bpy.ops.transform.rotate(value=radians(-90),orient_axis='X')

		bpy.ops.transform.resize(value=(keel_length, 
								1, 
								self.the_hull.hull_height))
								
		# Shift vertically
		bpy.ops.transform.translate(value=(0,0,-self.the_hull.hull_height/2))

		bpy.ops.object.transform_apply(scale=True,location=False)
		
		self.keel_object=bpy.context.view_layer.objects.active
		self.keel_object.name="Keel.s%0.2f"%(self.lateral_offset)


		bpy_helper.select_object(self.keel_object,True)
		bpy_helper.move_object_to_collection(self.view_keel_collection,self.keel_object)

		bpy_helper.select_object(self.keel_object,True)
		bpy.ops.object.mode_set(mode='EDIT')
		bpy.ops.mesh.select_all(action='SELECT')

		#if self.lateral_offset>0:
		#	bpy.ops.mesh.normals_make_consistent(inside=True)
		#else:
		#	bpy.ops.mesh.normals_make_consistent(inside=False)

		bpy.ops.object.mode_set(mode='OBJECT')

		bool_new = self.keel_object.modifiers.new(type="BOOLEAN", name="bool.hull_shape")
		bool_new.object = self.the_hull.hull_object
		bool_new.operation = 'INTERSECT'
		bool_new.use_self=1


		bpy_helper.select_object(self.keel_object,True)
		#bpy.ops.object.modifier_apply(modifier=bool_new.name)

		#bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

		modifier=self.keel_object.modifiers.new(name="solidify", type='SOLIDIFY')


		#if self.lateral_offset>0:
		modifier.thickness=self.thickness
		#thickness_shift
		#else:
		#	modifier.thickness=-thickness_shift

		bpy.context.view_layer.objects.active = self.keel_object
		#bpy.ops.object.modifier_apply(modifier=modifier.name)


		# =====================================================
		# Make Keel Slicer for notches
		# =====================================================
		bpy.ops.mesh.primitive_cube_add(size=cube_size, 
			enter_editmode=False, 
			location=(  self.station_start+keel_length/2, 
						self.lateral_offset, 
						self.top_height))
		

		bpy.ops.transform.resize(value=(keel_length, 
								self.thickness, 
								self.the_hull.hull_height))

		bpy.ops.transform.translate(value=(0,0,-self.the_hull.hull_height/2-(self.slicer_cut_height)))

		bpy.ops.object.transform_apply(scale=True,location=False)
		
		self.keel_slicer_object=bpy.context.view_layer.objects.active
		self.keel_slicer_object.name="Keel_Slicer.s%0.2f"%(self.lateral_offset)
		self.keel_slicer_object.display_type="WIRE"
		self.keel_slicer_object.hide_render = True
		#self.keel_slicer_object.hide_viewport = True

		bpy_helper.select_object(self.keel_slicer_object,True)
		bpy_helper.move_object_to_collection(self.view_keel_collection,self.keel_slicer_object)


		bool_new = self.keel_slicer_object.modifiers.new(type="BOOLEAN", name="bool.hull_shape")
		bool_new.object = self.the_hull.hull_object
		bool_new.operation = 'INTERSECT'

		bpy_helper.select_object(self.keel_slicer_object,True)
		#bpy.ops.object.modifier_apply(modifier=bool_new.name)

		bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='MEDIAN')

		return self.keel_object



class keel_builder:
	the_hull=None

	keel_screw_positions=[]
	keel_screws=[]

	top_height=0


	# screw size in MM
	target_screw_size=10 # target size in output model

	# how big to make screws in computer model so they output correctly when scaled output
	# hull object has hull_scale object for scale models...
	scaled_screw_size=10 

	def __init__(self,the_hull):
		self.the_hull=the_hull

	def make_screws(self):

		scaleup_factor=1/self.the_hull.hull_output_scale

		# scale and convert from MM to M (divide / 1000) which is what blender uses for units
		self.scaled_screw_size=self.target_screw_size*scaleup_factor/1000

		screw_top_height=self.top_height-self.scaled_screw_size


		for screw_position in self.keel_screw_positions:
			bpy.ops.mesh.primitive_cylinder_add(radius=self.scaled_screw_size/2, depth=5, enter_editmode=False, location=[0,0,0])
			screw_object=bpy.context.view_layer.objects.active
			screw_object.name="screw_keel_%02.2f"%(screw_position)
			screw_object.location.x=screw_position
			screw_object.location.z=screw_top_height
			bpy.ops.transform.rotate(value=radians(90),orient_axis='X')
			self.keel_screws.append(screw_object)

			#bpy_helper.move_object_to_collection(the_keel.view_keel_collection,screw_object)

			for keel in self.the_hull.keels:
				if keel.keel_object!=None:
					bool_new = keel.keel_object.modifiers.new(type="BOOLEAN", name="screw%02.2f"%screw_position)
					bool_new.object = screw_object
					bool_new.operation = 'DIFFERENCE'

			screw_object.hide_viewport=True


	def make_segmented_keel(self,top_height,slicer_cut_height=0.2,start_bulkhead=1,end_bulkhead=4):
		overlap_factor=0.2  # 20% overlap

		self.top_height=top_height

		overlap_distance=self.the_hull.bulkhead_spacing*overlap_factor #actual overlap distance
		half_overlap_distance=overlap_distance/2
		end_segment_length=self.the_hull.bulkhead_spacing*1.5+half_overlap_distance
		full_segment_length=self.the_hull.bulkhead_spacing*2+overlap_distance


		#finish_eval_location=2+self.the_hull.bulkhead_thickness
		#current_eval_location=self.the_hull.start_bulkhead_location-self.the_hull.bulkhead_thickness

		current_eval_location=self.the_hull.start_bulkhead_location #+(self.the_hull.bulkhead_spacing*start_bulkhead)
		finish_eval_location=self.the_hull.start_bulkhead_location+(self.the_hull.bulkhead_spacing*end_bulkhead)

		current_eval_location-=self.the_hull.bulkhead_thickness
		finish_eval_location+=self.the_hull.bulkhead_thickness



		odd_spacing=True

		keel_middle_space=0.2
		keel_thickness=0.1 #self.the_hull.bulkhead_thickness

		lateral_offset=0
		segment_index=0

		#print("overlap: %f")

		print("keel end segment: %f full segment: %f"%(end_segment_length,full_segment_length))

		# check for < 50 to prevent runaway
		while current_eval_location<finish_eval_location and segment_index<50:

			if odd_spacing==True:
				lateral_offset=keel_middle_space/2+keel_thickness*0
				odd_spacing=False
			else:
				lateral_offset=keel_middle_space/2+keel_thickness*1
				odd_spacing=True

			if (current_eval_location+full_segment_length<=finish_eval_location) and segment_index!=0:
				print("currenteval: %f full length"%current_eval_location)

				the_keel = keel(self.the_hull,
						lateral_offset=lateral_offset,
						top_height=self.top_height,
						station_start=current_eval_location,
						station_end=current_eval_location+full_segment_length)

				the_keel.make_keel(keel_thickness)
				self.the_hull.integrate_keel(the_keel)

				the_keel = keel(self.the_hull,
						lateral_offset=-lateral_offset,
						top_height=self.top_height,
						station_start=current_eval_location,
						station_end=current_eval_location+full_segment_length)

				the_keel.make_keel(keel_thickness)
				self.the_hull.integrate_keel(the_keel)

				current_eval_location+=full_segment_length-overlap_distance

				self.keel_screw_positions.append(current_eval_location+half_overlap_distance)

				

				# screw_positions.append(current_eval_location-half_overlap_distance)

			else: # try end segment
				print("currenteval: %f remainder"%current_eval_location)

				if segment_index==0:
					station_end=current_eval_location+end_segment_length
				else:
					station_end=finish_eval_location
					
				the_keel = keel(self.the_hull,
						lateral_offset=lateral_offset,
						top_height=self.top_height,
						station_start=current_eval_location,
						station_end=station_end)

				the_keel.make_keel(keel_thickness)
				self.the_hull.integrate_keel(the_keel)	

				the_keel = keel(self.the_hull,
						lateral_offset=-lateral_offset,
						top_height=self.top_height,
						station_start=current_eval_location,
						station_end=station_end)

				the_keel.make_keel(keel_thickness)
				self.the_hull.integrate_keel(the_keel)	

				if segment_index==0:
					current_eval_location+=end_segment_length-overlap_distance
					self.keel_screw_positions.append(current_eval_location+half_overlap_distance)
					print("add end length")
				else:
					current_eval_location=finish_eval_location
					print("skip to end")

				#if current_eval_location+end_segment_length>=finish_eval_location:
					
				#else:
					
				#	screw_positions.append(current_eval_location-half_overlap_distance)
		#	else:
		#		# fill the gap with whatever is left and finish
		#		new_longitudal=chine_helper.longitudal_element(z_offset=z_offset,width=-0.13,thickness=segment_thickness)
		#		new_longitudal.set_limit_x_length(current_eval_location,finish_eval_location)
		#		new_chine.add_longitudal_element(new_longitudal)
		#		current_eval_location=finish_eval_location

			segment_index+=1

			print("currenteval: %f finishval: %f segindex: %d"%(current_eval_location,finish_eval_location,segment_index))


