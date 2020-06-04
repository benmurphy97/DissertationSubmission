import pandas as pd
import numpy as np 
import time
import pickle
from background import get_popular_items, get_value_of_max_key_of_dict_of_tuple

class WCI():
    
    def __init__(self, window=10, n_pages=15,
                n_potential=2, p_threshold=.2, 
                rating_weight=2, ratings_threshold=0):

        self.window = window
        self.n_pages = n_pages
        self.n_potential = n_potential
        self.p_threshold = p_threshold
        self.rating_weight = rating_weight
        self.ratings_threshold = ratings_threshold


    # user_item_rating_matrix - every row is a user, every column is a movie
    # cluster_memberships - key:value, cluster_number:cluster_items
    # item_similarity_matrix - similarity matrix of items

    # what we need in the algorithm:
    #  - items in each cluster
    #  - ratings given be each to user to each item, 0 if no rating
    # - similarity matrix of items
    def fit(self, user_item_rating_matrix, item_cluster_memberships, item_similarity_matrix):
        start = time.time()
        print("******* Fitting *******")

        # popular_items is a dictionary of key value pairs
        # there is one pair for each cluster
        # the key is the cluster number
        # the value is a key value tuple
        # the tuple
        
        clustered_items = get_popular_items(user_item_rating_matrix, item_cluster_memberships)

        # potential_items next item to show based on potential
        potential_items = {}

        item_similarity_matrix = np.array(item_similarity_matrix)

        user_number_items_found = []

        # put loop in for all users
        # for a_user in range(len(user_item_rating_matrix)):
        # for a_user in range(1000):
        for a_user in np.random.choice(len(user_item_rating_matrix), 500, replace=False):


            # for this user:
            user = a_user
            # print("\nUser: ", user)

            # get vector of ratings
            user_rating_vector = user_item_rating_matrix[user]
            # print("User rating vector", user_rating_vector[0:30])

            numpy_vector = np.array(user_rating_vector)
            elements_above_threshold = numpy_vector[numpy_vector>self.ratings_threshold]
            # print("Nunber of items above ratings_threshold: ", len(elements_above_threshold))

            # number of items found above ratings threshold
            items_above_ratings_threshold_found = 0


            # dictionary to store the similarity matrices of the cluster
            similarity_matrix_dict = {}

            # make a copy of the clustered_items items
            temp_clustered_items = clustered_items.copy()
            # make a copy of the potential items
            temp_potential_items = potential_items.copy()

            # for the number of pages to show
            for page in range(self.n_pages):
                # print("\nWindow ", page, "\n")
                # print(f"\nPAGE: {page}, Potential Items: {temp_potential_items}")

                # get number of potential items in our dict
                potential_items_count = len(temp_potential_items)
                clustered_items_count = len(temp_clustered_items)

                # if there are less items in potential dict than what we need
                if potential_items_count <= self.n_potential:
                    # set p_items_window to the number of items in the potential dict
                    p_items_window = potential_items_count
                # else if there is enough for what we need
                else:
                    # number of potential_items is the default value of n_potential
                    p_items_window = self.n_potential

                # and set c_items_window to the window minus p_items_window if there are enough movies in the popular dictionary
                c_items_window = self.window - p_items_window

                # if there are fewer items in the dict than what we need
                if clustered_items_count <= c_items_window:
                    # set c_items_window to the number of items in the popular dict
                    c_items_window = clustered_items_count
                else:
                    pass
                    # leave it as the original value of c_items_window

                # if both dicts are empty, break the loops
                if clustered_items_count==0 and potential_items_count==0:
                    # get out of loop
                    # print("Exhausted the dicts")
                    break

                # print("Clustered items window: ",c_items_window,"\nPotential items window: ", p_items_window)


                # we must get the window items in their current state before changes our made to the dict as we are displaying 4 items in one go
                # window items will be a list of tuples with length of the window
                # each tuple will be a key-value pair with (cluster number, global item index)
                window_items = []
                for gi in range(c_items_window):
                    a, b, temp_clustered_items = get_value_of_max_key_of_dict_of_tuple(temp_clustered_items)
                    window_items.append((a, b))

                for pi in range(p_items_window):
                    a, b, temp_potential_items = get_value_of_max_key_of_dict_of_tuple(temp_potential_items)
                    window_items.append((a, b))


                # print("Window items: ", window_items)

                # now we go through each window item and see if the user has consumed the item
                for wind_item in window_items:

                    cluster_number_with_item = wind_item[0]
                    global_key_of_item = wind_item[1]
                    
                    # cluster_number_with_item, item_key_of_max, temp_popular_items =  get_value_of_max_key_of_dict_of_tuple(temp_general_items)

                    # if the user rating for the item is over threshold  
                    user_rating = user_rating_vector[global_key_of_item]
                    if user_rating > self.ratings_threshold:
                        # print("Found item above threshold")
                        items_above_ratings_threshold_found += 1

                        # get items in the cluster
                        items_in_cluster = item_cluster_memberships[cluster_number_with_item]
                        # print("Items in cluster:", items_in_cluster)

                        # if there is more than one item in the cluster
                        if len(items_in_cluster) > 1:
                            # print("Cluster Key: ",cluster_number_with_item, "This cluster has more than 1 member")

                            # check if the similarity matrix is in the dict already
                            if cluster_number_with_item in similarity_matrix_dict:
                                similarity_matrix_of_cluster = similarity_matrix_dict[cluster_number_with_item]
                            
                            # if we haven't got it before, create it, 
                            else:
                                similarity_matrix_of_cluster = np.array([i[items_in_cluster] for i in item_similarity_matrix[[items_in_cluster]]])
                                # turn 1s to 0, removing similarity of item to itself
                                similarity_matrix_of_cluster[similarity_matrix_of_cluster==1] = 0
                            
                            # update it using the rating that the user gave the movie
                            # we need to know what row we update, the index in the list the movie was 
                            cluster_position = items_in_cluster.index(global_key_of_item)
                            
                            # set row of movie rated to 0
                            similarity_matrix_of_cluster[cluster_position] = 0

                            # multiply column at item index by the rating / rating weight
                            similarity_matrix_of_cluster[:,cluster_position] *= (user_rating/self.rating_weight) # vertical weight updates
                            
                            # either create or replace the updated similarity matrix of cluster
                            similarity_matrix_dict[cluster_number_with_item] = similarity_matrix_of_cluster

                            # get mean weights
                            mean_potential_scores = [i.sum()/(len(i)-1) for i in similarity_matrix_of_cluster]

                            for i, v in enumerate(mean_potential_scores):
                                # the value will be 0 if we've already rated the item
                                # only add the item to the potential dict if its over the threshold
                                if v > 0 and v > self.p_threshold:
                                    # add the item to the potential dictionary
                                    temp_potential_items[cluster_number_with_item] = (mean_potential_scores, items_in_cluster[i])

                        # else there is only one movie in the cluster
                        else:
                            # dont add it to potential
                            pass
                    
                    else:
                        # we presented an item to the user that is below the rating threshold
                        pass

            user_number_items_found.append(items_above_ratings_threshold_found)

        total_time = time.time()-start
        # print("Time taken(s): ", round(total_time, 5))   

       
        user_number_items_found = np.array(user_number_items_found)

        return user_number_items_found.mean()



user_rating_matrix = np.load('/Users/benmurphy/OneDrive/Projects/Nebflix/DataProcessing/Pickles/user_rating_matrix.npy')  

sim_matrix = pd.read_pickle('/Users/benmurphy/OneDrive/Projects/Nebflix/DataProcessing/Pickles/cos_sim_df.pkl')

with open('/Users/benmurphy/OneDrive/Projects/Nebflix/DataProcessing/Pickles/cluster_dict.pickle', 'rb') as handle:
    cluster_dict = pickle.load(handle)

print(user_rating_matrix.shape)


# list to create df
testing_list = []

p_thresholds = [0.2, 0.3, 0.4]

for n_pages in range(5,15):

    for n_potential in range(0,6):


        print(f"\nN pages: {n_pages}")

        wci = WCI(n_pages=n_pages, n_potential=n_potential, window=10)

        # call the fit method returning the average number of items found by the method
        avg_items_found = wci.fit( user_item_rating_matrix = user_rating_matrix,

                                        item_cluster_memberships = cluster_dict,

                                        item_similarity_matrix=sim_matrix
                                        )

        print("DEBUG", avg_items_found)

        test_dict = {
            "n_pages": n_pages,
            "n_potential": n_potential,
            "window":10,
            "user_number_items_found": avg_items_found
        }  

        testing_list.append(test_dict)


testDF = pd.DataFrame(testing_list)

testDF.to_csv('/Users/benmurphy/OneDrive/Projects/Nebflix/WebApp/Nebflix/WeightedClusteredItems/TestResults/testingWCI.csv', index=False)
