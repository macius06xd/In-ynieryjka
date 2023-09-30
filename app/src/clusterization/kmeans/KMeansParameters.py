class KMeansParameters:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KMeansParameters, cls).__new__(cls)
            # Default values for K-means parameters
            cls._instance.init = 'k-means++'
            cls._instance.n_init = 10
            cls._instance.max_iter = 300
            cls._instance.tol = 1e-4
            cls._instance.random_state = 1
            cls._instance.precompute_distances = True
            cls._instance.algorithm = 'auto'
            cls._instance.n_jobs = None
            cls._instance.verbose = 0

        return cls._instance
