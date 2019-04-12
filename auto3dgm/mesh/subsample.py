"""
TODO: Please fix this comment
"Subsample (Class with Instance Attributes and Methods, and Static Methods)"
"Class summary: Subsamples one or more meshes"
"Constructor input: Optional parameters including…Number of points Subsample methodSet of meshes"
"Instance attributes: Number of points Subsample method Set of meshes"
"Instance methods: "
"prepare_analysis "
"Receives one or more meshes, and optionally number of points and subsampling method"
"Sets parameters and meshes as object attributes"
"Calls and returns result of export_analysis"
"export_analysis"
"Returns a data object capable of being input into JobRun. "
"This data object could be something like a dict similar to "
"{‘data’: {‘a’: mesh1, ‘b’: mesh2, ‘c’: mesh3, etc.}, "
" ‘params’: {‘point_number’: 200, ‘subsample_method’: ‘GPR’}, ‘func’: function_reference }"
"process_result"
"Receives a JubRun output data object, and returns the dict of Mesh objects included with that"
"Static methods:"
"Methods specific to each subsampling algorithm, each method receives a mesh "
"and number of points and returns a subsampled mesh"
"""

import vtk 
from numpy import all, amin, any, argmax, array, isclose, ndarray, where, empty
import random
from scipy.spatial.distance import cdist
from auto3dgm.mesh.mesh import Mesh
from auto3dgm.mesh.meshfactory import MeshFactory
import numpy as np
from auto3dgm import jobrun
from auto3dgm.jobrun import jobrun
from auto3dgm.jobrun import job
from auto3dgm.jobrun.jobrun import JobRun
from auto3dgm.jobrun.job import Job

class Subsample:
    def __init__(self, pointNumber=None, method=None, meshes=None):
        self.pointNumber=pointNumber
        self.method=method
        self.meshes=meshes
        ret = {}
        seed = {}
        for singlePoint in self.pointNumber:
            #assumes all entries in list of pointNumbers are unique
            job = self.prepare_analysis(point_number=singlePoint, method=method, seed=seed)
            results = self.export_analysis(job=job)
            ret[singlePoint] = {'output': results}
            for key in results:
                #keys should be mesh names
                seed[key] = results[key].vertices

        return ret


    def prepare_analysis(self, point_number=None, method='FPS', seed=None):
        #Create Job
        job_data = Subsample.generate_data(meshes=self.meshes)
        job_params = Subsample.generate_params(point_number=point_number, subsample_method=self.method, seed=seed)
        job_func = self.generate_func(method=method)
        return Job(data=job_data, params=job_params, func=job_func)


    @staticmethod    
    def generate_data(meshes=None):
        #mesh name or index value or something like that
        '''
        {
        'mesh0.name': {‘mesh’: mesh0}, 
        'mesh1.name': {‘mesh’: mesh1}, 
        'mesh2.name': {‘mesh’: mesh2}
        }, 
        '''
        ret = {}
        s = 'analysis_'
        for index, mesh in enumerate(meshes):
            #temp_s = s + str(index)
            ret[mesh.name] = {'mesh': mesh}
        return ret

    @staticmethod
    def generate_params(point_number=None, subsample_method=None, seed=None):
        #dict of params, issue with the fucntion reference?
        '''
        {
            'n': 200, 
            'seed': {
                mesh1.name: previous subsample output for mesh1
                mesh2.name: previous subsample output for mesh2
                }
        }
        '''
        ret = {}
        ret['n'] = point_number
        if seed is not None:
            ret['seed'] = seed
        else:
            ret['seed'] = empty([0,0])
        return ret

    def generate_func(self, func='FPS'):
        if func == 'FPS':
            return self.far_point_subsample
        if func == 'GPL':
            return self.gpl_subsample

    ## class method
    @staticmethod
    def export_analysis(job=None):
        jobrun = JobRun(job=job)
        return jobrun.execute_jobs()

    @staticmethod
    def far_point_subsample(mesh, n, seed=None):
        # seed should be a list of points 3x previous n
        # return val is mesh object that I wrote
        # seed = previous mesh.verticies
        #edited this method so that the correct previous seed is extracted from the params dict, since the architecture forces the entire dict to be passed down
        v = mesh.vertices
        seed_t = seed[mesh.name]
        if n > v.shape[0] or n < seed_t.shape[0]:
            raise ValueError('n larger than number of vertices or smaller than number of seed_t points')
        if isinstance(seed_t, ndarray) and seed_t.size:
            if v.shape[1] == 3 and v.ndim == 2:
                # are s in v (or close enough?)
                if all([any(all(isclose(x, v), 1)) for x in seed_t]):
                    # get ind for seed_t points
                    seedint = [where(all(isclose(x, v), axis=1))[0][0] for x in seed_t]
            else:
                raise ValueError('seed improperly formed, expecting n x 3 array')
        else:
            random.seed()
            seedint = [random.randint(0, v.shape[0]-1)]
        subint = seedint
        for i in range(len(subint),n):
            subint.append(argmax(amin(cdist(v[subint], v), axis=0)))
        # list of integers that subsampled
        return MeshFactory.mesh_from_data(v[subint])

    # far_point_subsample('mesh') TODO: What is this
     
    # TODO: All of this causes errors because of Matlab syntax
    # @staticmethod
    # def gpl_subsample(mesh, n, seed=empty([0,0])):
    #     v = mesh.vertices
    #     if n > v.shape[0] or n < seed.shape[0]:
    #         raise ValueError('n larger than number of vertices or smaller than number of seed points')
    #     f=mesh.faces
    #     nV=np.size(v,1)
    #     Center = np.mean(v, axis=1)
    #     v = v - np.matlib.repmat(Center, 1, nV)
    #     Area = compute_surface_area(np.transpose(v),np.transpose(f))
    #     v = v * sqrt(1/Area)
    #     curvature = findPointNormals(np.transpose(v),10)
    #     Lambda = curvature/np.sum(curvature)
    #     I = np.array([F[1,:], F[2,:],F[3,:]])
    #     J = np.array([F[2,:], F[3,:],F[1,:]])
    #     E = np.array([[I], [J]])

    #     EdgeIdxI = E[1,:]
    #     EdgeIdxJ = E[2,:]
    #     bandwidth = np.mean(np.sqrt(np.sum((V(:,EdgeIdxI)-V(:,EdgeIdxJ)).^2)))/5

    # @staticmethod
    # def compute_surface_area(mesh):
    #     v = mesh.vertices
    #     f = mesh.faces
    #     L1 = np.sqrt(np.sum((v[F[:,2],:]-V[F[:,3],:]).^2,2));
    #     L2 = np.sqrt(np.sum((v[F[:,1],:]-V[F[:,3],:]).^2,2));
    #     L3 = np.sqrt(np.sum((v[F[:,1],:]-V[F[:,2],:]).^2,2));
    #     S=(L1+L2+L3)/2;
    #     TriArea=np.sqrt(np.absolute(S.*(S-L1).*(S-L2).*(S-L3)));
    #     Area=np.sum(TriArea);

