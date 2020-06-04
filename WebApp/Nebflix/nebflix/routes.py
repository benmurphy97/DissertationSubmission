import os
import secrets
from flask import render_template, url_for, flash, redirect, request, abort
from flask import jsonify, request
from nebflix import app, mongo, graph
from nebflix.forms import SearchMovieForm, AlgorithmForm
from nebflix.classes.movie import Movie


@app.route("/")
@app.route("/home")
def home():
	return render_template('home.html')

# creates link from user to one movie in each cluster
@app.route('/create_Clustered_Item_relationships')
def create_Clustered_Item_relationships():

	user_name = "Ben"
	# query to count the number of clusters in the graph
	query = '''
			match (c:Cluster)
			return count(c) as count
			'''

	# run the query on our graph
	queryResult = graph.run(query)

	# convert output to a dict
	queryResultDict = queryResult.data()
	num_clusters = queryResultDict[0]['count']

	# loops through the cluster numbers
	# gets the item with the most ratings in the cluster
	# creates the Clustered_Item relationship with the averageRatings in the cluster as the property
	for i in range(num_clusters):

		query = '''match (u:User {{name:"{0}"}})
					match (m:Movie)-[:isMemberOf]-(c:Cluster{{clusterId:{1}}})
					with m,c,u,size(()-[:Rated]-(m)) as userCount
					with m,c,u,userCount order by userCount desc limit 1
					create (u)-[g:Clustered_Item{{clusterAverageRatings:c.averageRatings }}]->(m)
				'''.format(user_name, str(i))
		
		graph.run(query)

	return ''


# creates link from user to one movie in each cluster
@app.route('/algo_rate_potential', methods=['GET','POST'])
def algo_rate_potential():
	print('algo_rate_potential')

	user_name = 'Ben'
	

	for i in range(4):
		movieType = request.form[f'movie{i}type']
		movieid = request.form[f'movie{i}Id']
		rating = request.form[f'rating{i}']

		print("\nMovie ID: ", movieid,"\nRating: ",rating, "\nMovie type: ", movieType)

		if movieType == 'p':

			print("This is a potential movie: ", movieid)

			# query creates rated relationship and deletes clustered_item relationship
			potential_rate_query = '''
				match (u:User {{name: "{0}"}})-[p:Potential]-(m:Movie {{movieId: {1}}})
				create (u)-[r:Rated {{value: {2}}}]->(m)
				delete (p)
				'''.format(user_name, movieid, rating)
			graph.run(potential_rate_query)

			set_potential_query = '''
								match (u:User {{name:"{0}"}})
								match (:Movie{{movieId: {1}}})-[:ConnectedTo]-(ms:Movie)
								unwind ms.movieId as targetMovieId
								match (m:Movie{{movieId:targetMovieId}})-[con:ConnectedTo]-(movies:Movie)
								where not (u)-[:Rated]-(m)
								with u, movies as movies, m, con
								optional match (u)-[rate:Rated]-(movies)
								with u,avg(COALESCE(rate.value, 1) * (con.similarity) / 2) as value, m
								match (u)-[p:Potential]-(m)
								set p.weight = value
								'''.format(user_name, movieid)

			graph.run(set_potential_query)
		
		elif movieType == 'c':

			print("This is a clustered item movie: ", movieid)

			cItem_rate_query = '''
								match (u:User {{name: "{0}"}})-[g:Clustered_Item]-(m:Movie {{movieId: {1}}})
								create (u)-[r:Rated {{value: {2}}}]->(m)
								delete (g)
								'''.format(user_name, movieid, rating)
			graph.run(cItem_rate_query)

			create_potential_query = '''
					match (u:User {{name:"{0}"}})
					match (:Movie{{movieId: {1}}})-[:ConnectedTo]-(ms:Movie)
					unwind ms.movieId as targetMovieId

					match (m:Movie{{movieId:targetMovieId}})-[con:ConnectedTo]-(movies:Movie)
					with u, movies as movies, m, con
					optional match (u)-[rate:Rated]-(movies)
					with u,avg(COALESCE(rate.value, 1) * (con.similarity) / 2) as value, m
					create (u)-[p:Potential{{weight:value}}]->(m)
					'''.format(user_name, movieid)

			graph.run(create_potential_query)
			
	# return redirect(url_for('algo_create_potential'))
	return redirect('WCI')
	
@app.route("/WCI", methods=['GET'])
def WCI():

	user_name = 'Ben'

	window = 4
	numberPotentialMovies = 2

	# query for the potential movies 
	query = '''
			match (u:User {{name:"{0}"}})-[p:Potential]-(m:Movie)
			where not (u)-[:RATED]-(m) AND p.weight > .5
			return m.movieId,p.weight 
			order by p.weight desc
			LIMIT {1}
			'''.format(user_name, numberPotentialMovies)
			
	# run the query on the graph
	potentialQueryResult = graph.run(query)

	# get the number of Potential movies that were found in the query
	potentialQueryResultDict = potentialQueryResult.data()
	resultsCount = len(potentialQueryResultDict)

	movie_objects = []

	# if the number of Potential movies is greater than 0
	if resultsCount>0:

		# movieIds of the Potential movies
		potential_movie_ids = [i['m.movieId'] for i in potentialQueryResultDict]

		# query mongodb to get the data about the Potential movies
		data = mongo.db.movies.find({'movieId': {'$in': potential_movie_ids}})

		# create Movie objects data retrieved from mongodb
		movie_objects += [Movie( movieId=i['movieId'],
						title=i['title'], 
						image_link=i['image_link'],
						storyline=i['storyline'],
						director=i['director'],
						algo_type='p') for i in data]


	clusteredItems2get = window-resultsCount
	# query for clustered_item
	query = '''
			match (u:User {{name:"{0}"}})-[g:Clustered_Item]-(m:Movie)
			where not (u)-[:RATED]-(m)
			return m.movieId,g.clusterAverageRatings 
			order by g.clusterAverageRatings desc
			LIMIT {1}
			'''.format(user_name, clusteredItems2get)

	# run the query on our graph
	clusterItemQueryResult = graph.run(query)
	clusterItemQueryResultDict = clusterItemQueryResult.data()

	# get the movieIds from our dict, list of ints 
	clustered_item_movie_ids = [i['m.movieId'] for i in clusterItemQueryResultDict]
	print("Clustered item movie ids: ", clustered_item_movie_ids)
	# query our mongo movies collection for our list of ids
	data = mongo.db.movies.find({'movieId': {'$in': clustered_item_movie_ids}})

	# create Movie objects with the documents from our query
	movie_objects += [Movie( movieId=i['movieId'],
					title=i['title'], 
					image_link=i['image_link'],
					storyline=i['storyline'],
					director=i['director'],
					algo_type='c') for i in data]

	# get images from movie_objects

	return render_template('WCI.html', 
							movie0=movie_objects[0],
							movie1=movie_objects[1],
							movie2=movie_objects[2],
							movie3=movie_objects[3])

