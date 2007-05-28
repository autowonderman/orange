/*
    This file is part of Orange.

    Orange is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Orange is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Orange; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

    Author: Miha Stajdohar, 1996--2002
*/


#include "ppp/networkoptimization.ppp"

TNetworkOptimization::TNetworkOptimization()
{
	//cout << "constructor" << endl;
	import_array();
	
	nVertices = 0;
	nLinks = 0;

	k = 1;
	k2 = 1;
	width = 10000;
	height = 10000;
	links = NULL;
	pos = NULL;
	temperature = sqrt(width*width + height*height) / 10;
	coolFactor = 0.96;
}

#ifdef _MSC_VER
#if _MSC_VER < 1300
template<class T>
inline T &min(const T&x, const T&y)
{ return x<y ? x : y; }
#endif
#endif

TNetworkOptimization::~TNetworkOptimization()
{
	//cout << "destructor" << endl;
	free_Links();
	free_Carrayptrs(pos);
	Py_DECREF(coors);
}

void TNetworkOptimization::dumpCoordinates()
{
	int rows = nVertices;
	int columns = 2;

	for (int i = 0; i < rows; i++)
	{
		for (int j = 0; j < columns; j++)
		{
			cout << pos[i][j] << "  ";
		}

		cout << endl;
	}
}

void TNetworkOptimization::random()
{
	srand(time(NULL));

	int i;
	for (i = 0; i < nVertices; i++)
	{
		pos[i][0] = rand() % (int)width;
		pos[i][1] = rand() % (int)height;
	}
}

static int julery_isqrt(int val) {
	    int temp, g=0, b = 0x8000, bshft = 15;
	    do {
	        if (val >= (temp = (((g << 1) + b)<<bshft--))) {
	           g += b;
	           val -= temp;
	        }
	    } while (b >>= 1);
	    return g;
	}

int TNetworkOptimization::fruchtermanReingold(int steps)
{
	/*
	cout << "nVertices: " << nVertices << endl << endl;
	dumpCoordinates();
	/**/
	double **disp = (double**)malloc(nVertices * sizeof (double));
	int i = 0;
	for (i = 0; i < nVertices; i++)
	{
		disp[i] = (double *)calloc(2, sizeof(double));

		if (disp[i] == NULL)
		{
			cerr << "Couldn't allocate memory (disp[])\n";
			return 1;
		}
	}

	int count = 0;
	double kk = 1;
	double localTemparature = 5;
	double area = width * height;

	k2 = area / nVertices;
	k = sqrt(k2);
	kk = 2 * k;
	double kk2 = kk * kk;

	// iterations
	for (i = 0; i < steps; i++)
	{
		//cout << "iteration: " << i << endl;
		// reset disp
		int j = 0;
		for (j = 0; j < nVertices; j++)
		{
			disp[j][0] = 0;
			disp[j][1] = 0;
		}

		int v = 0;
		// calculate repulsive force
		//cout << "repulsive" << endl;
		for (v = 0; v < nVertices - 1; v++)
		{
			for (int u = v + 1; u < nVertices; u++)
			{
				double difX = pos[v][0] - pos[u][0];
				double difY = pos[v][1] - pos[u][1];

				double dif2 = difX * difX + difY * difY; 

				if (dif2 < kk2)
				{
					if (dif2 == 0)
						dif2 = 1;

					double dX = difX * k2 / dif2;
					double dY = difY * k2 / dif2;

					disp[v][0] = disp[v][0] + dX;
					disp[v][1] = disp[v][1] + dY;

					disp[u][0] = disp[u][0] - dX;
					disp[u][1] = disp[u][1] - dY;
				}
			}
		}
		// calculate attractive forces
		//cout << "attractive" << endl;
		for (j = 0; j < nLinks; j++)
		{
			int v = links[j][0];
			int u = links[j][1];

			double difX = pos[v][0] - pos[u][0];
			double difY = pos[v][1] - pos[u][1];

			double dif = sqrt(difX * difX + difY * difY);

			double dX = difX * dif / k;
			double dY = difY * dif / k;

			disp[v][0] = disp[v][0] - dX;
			disp[v][1] = disp[v][1] - dY;

			disp[u][0] = disp[u][0] + dX;
			disp[u][1] = disp[u][1] + dY;
		}
		//cout << "limit" << endl;
		// limit the maximum displacement to the temperature t
		// and then prevent from being displaced outside frame
		for (v = 0; v < nVertices; v++)
		{
			double dif = sqrt(disp[v][0] * disp[v][0] + disp[v][1] * disp[v][1]);

			if (dif == 0)
				dif = 1;

			pos[v][0] = pos[v][0] + (disp[v][0] * min(abs(disp[v][0]), temperature) / dif);
			pos[v][1] = pos[v][1] + (disp[v][1] * min(abs(disp[v][1]), temperature) / dif);

			//pos[v][0] = min((double)width,  max((double)0, pos[v][0]));
			//pos[v][1] = min((double)height, max((double)0, pos[v][1]));
		}
		//cout << temperature << ", ";
		temperature = temperature * coolFactor;
	}

	//cout << "end coors: " << endl;
	//dumpCoordinates();

	// free space
	for (i = 0; i < nVertices; i++)
	{
		free(disp[i]);
		disp[i] = NULL;
	}
	//cout << endl;
	free(disp);
	disp = NULL;
	
	return 0;
}

#include "externs.px"
#include "orange_api.hpp"

PyObject *NetworkOptimization_new(PyTypeObject *type, PyObject *args, PyObject *keyw) BASED_ON (Orange, "(Graph) -> None") 
{
	PyObject *pygraph;
	
	if (PyArg_ParseTuple(args, "O:GraphOptimization", &pygraph))
	{
		TGraphAsList *graph = &dynamic_cast<TGraphAsList &>(PyOrange_AsOrange(pygraph).getReference());

		if (graph->nVertices < 2)
		  PYERROR(PyExc_AttributeError, "graph has less than two nodes", NULL);

		//return WrapNewOrange(new TGraphOptimization(graph->nVertices, pos, nLinks, links), type);
		return WrapNewOrange(new TNetworkOptimization(), type);
	}
	else
	{
		return WrapNewOrange(new TNetworkOptimization(), type);
	}
}
/* ==== Free a double *vector (vec of pointers) ========================== */ 
void TNetworkOptimization::free_Carrayptrs(double **v)  {

	free((char*) v);
}

/* ==== Allocate a double *vector (vec of pointers) ======================
    Memory is Allocated!  See void free_Carray(double ** )                  */
double **TNetworkOptimization::ptrvector(double n)  {
	double **v;
	v=(double **)malloc((size_t) (n*sizeof(double)));

	if (!v)   {
		printf("In **ptrvector. Allocation of memory for double array failed.");
		exit(0);  
	}
	return v;
}

/* ==== Create Carray from PyArray ======================
    Assumes PyArray is contiguous in memory.
    Memory is allocated!                                    */
double **TNetworkOptimization::pymatrix_to_Carrayptrs(PyArrayObject *arrayin)  {
	double **c, *a;
	int i,n,m;
	
	n = arrayin->dimensions[0];
	m = arrayin->dimensions[1];
	c = ptrvector(n);
	a = (double *) arrayin->data;  /* pointer to arrayin data as double */
	
	for (i = 0; i < n; i++) {
		c[i] = a + i * m;
	}

	return c;
}

/* ==== Create 1D Carray from PyArray ======================
 129     Assumes PyArray is contiguous in memory.             */
bool *TNetworkOptimization::pyvector_to_Carrayptrs(PyArrayObject *arrayin)  {
	int n;

	n = arrayin->dimensions[0];
	return (bool *) arrayin->data;  /* pointer to arrayin data as double */
}

int TNetworkOptimization::setGraph(TGraphAsList *graph)
{
	//cout << "-1" << endl;
	free_Links();
	free_Carrayptrs(pos);

	nVertices = graph->nVertices;
	int dims[2];
	dims[0] = nVertices;
	dims[1] = 2;
	//cout << "0" << endl;
	coors = (PyArrayObject *) PyArray_FromDims(2, dims, NPY_DOUBLE);
	pos = pymatrix_to_Carrayptrs(coors);

	random();
 
	//dumpCoordinates();
	nLinks = 0;
	int v;
	for (v = 0; v < graph->nVertices; v++)
	{
		TGraphAsList::TEdge *edge = graph->edges[v];

		if (edge != NULL)
		{
			int u = edge->vertex;
			links = (int**)realloc(links, (nLinks + 1) * sizeof(int));
			//cout << "1" << endl;
			if (links == NULL)
			{
				cerr << "Couldn't allocate memory (links 1)\n";
				return 1;
			}

			links[nLinks] = (int *)malloc(2 * sizeof(int));
			//cout << "2" << endl;
			if (links[nLinks] == NULL)
			{
				cerr << "Couldn't allocate memory (links[] 1)\n";
				return 1;
			}

			links[nLinks][0] = v;
			links[nLinks][1] = u;
			nLinks++;

			TGraphAsList::TEdge *next = edge->next;
			while (next != NULL)
			{
				int u = next->vertex;

				links = (int**)realloc(links, (nLinks + 1) * sizeof (int));
				//cout << "3" << endl;
				if (links == NULL)
				{
					cerr << "Couldn't allocate memory (links 2)\n";
					return 1;
				}

				links[nLinks] = (int *)malloc(2 * sizeof(int));
				//cout << "4" << endl;
				if (links[nLinks] == NULL)
				{
					cerr << "Couldn't allocate memory (links[] 2)\n";
					return 1;
				}

				links[nLinks][0] = v;
				links[nLinks][1] = u;
				nLinks++;

				next = next->next;
			}
		}
	}
	//cout << "5" << endl;
	return 0;
}

int getWords(string const& s, vector<string> &container)
{
    int n = 0;
	bool quotation = false;
    string::const_iterator it = s.begin(), end = s.end(), first;
    for (first = it; it != end; ++it)
    {
        // Examine each character and if it matches the delimiter
        if (((!quotation) && ((' ' == *it) || ('\t' == *it) || ('\r' == *it) || ('\f' == *it) || ('\v' == *it))) || ('\n' == *it))
        {
            if (first != it)
            {
                // extract the current field from the string and
                // append the current field to the given container
                container.push_back(string(first, it));
                ++n;
                
                // skip the delimiter
                first = it + 1;
            }
            else
            {
                ++first;
            }
        }
		else if (('\"' == *it) || ('\'' == *it))
		{
			if (quotation)
			{
				quotation = false;

				// extract the current field from the string and
                // append the current field to the given container
                container.push_back(string(first, it));
                ++n;
                
                // skip the delimiter
                first = it + 1;
			}
			else
			{
				quotation = true;

				// skip the quotation
				first = it + 1;
			}
		}
    }
    if (first != it)
    {
        // extract the last field from the string and
        // append the last field to the given container
        container.push_back(string(first, it));
        ++n;
    }
    return n;
}

PyObject *NetworkOptimization_setGraph(PyObject *self, PyObject *args) PYARGS(METH_VARARGS, "(Graph) -> None")
{
	PyObject *pygraph;

	if (!PyArg_ParseTuple(args, "O:NetworkOptimization.setGraph", &pygraph))
		return NULL;

	TGraphAsList *graph = &dynamic_cast<TGraphAsList &>(PyOrange_AsOrange(pygraph).getReference());

	CAST_TO(TNetworkOptimization, graphOpt);
	//cout << "networkoptimization.cpp/setGraph: setting graph..." << endl;
	if (graphOpt->setGraph(graph) > 0)
	{
		PYERROR(PyExc_SystemError, "setGraph failed", NULL);
	}
	//cout << "done." << endl;
	RETURN_NONE;
}

PyObject *NetworkOptimization_fruchtermanReingold(PyObject *self, PyObject *args) PYARGS(METH_VARARGS, "(steps, temperature) -> temperature")
{
	int steps;
	double temperature = 0;

	if (!PyArg_ParseTuple(args, "id:NetworkOptimization.fruchtermanReingold", &steps, &temperature))
		return NULL;

	CAST_TO(TNetworkOptimization, graph);

	graph->temperature = temperature;
	graph->coolFactor = exp(log(10.0/10000.0) / steps);
	
	if (graph->fruchtermanReingold(steps) > 0)
	{
		PYERROR(PyExc_SystemError, "fruchtermanReingold failed", NULL);
	}
	
	return Py_BuildValue("d", graph->temperature);
}

PyObject *NetworkOptimization_get_coors(PyObject *self, PyObject *args) /*P Y A RGS(METH_VARARGS, "() -> Coors")*/
{
	CAST_TO(TNetworkOptimization, graph);	
	Py_INCREF(graph->coors);
	return (PyObject *)graph->coors;  
}

PyObject *NetworkOptimization_getHubs(PyObject *self, PyObject *args) PYARGS(METH_VARARGS, "(n) -> HubList")
{
	int n;

	if (!PyArg_ParseTuple(args, "n:NetworkOptimization.getHubs", &n))
		return NULL;

	CAST_TO(TNetworkOptimization, graph);

	int *vertexPower = new int[graph->nVertices];

	int i;
	for (i=0; i < graph->nVertices; i++)
	{
		vertexPower[i] = 0;
	}

	for (i=0; i < graph->nLinks; i++)
	{
		vertexPower[graph->links[i][0]]++;
		vertexPower[graph->links[i][1]]++;
	}

	PyObject* hubList = PyList_New(n);
	
	for (i=0; i < n; i++)
	{
		int j;
		int ndx_max = -1;
		int max = 0;
		for (j=0; j < graph->nVertices; j++)
		{
			if (vertexPower[j] > max)
			{
				ndx_max = j;
				max = vertexPower[j];
			}
		}
		//cout << "pow: " << vertexPower[ndx_max] << " ndx: " << ndx_max << endl;

		vertexPower[ndx_max] = -2;
		PyList_SetItem(hubList, i, PyInt_FromLong(ndx_max));
	}

	delete [] vertexPower;
	return hubList;
}

PyObject *NetworkOptimization_closestVertex(PyObject *self, PyObject *args) PYARGS(METH_VARARGS, "(x, y) -> Ndx")
{
	double x;
	double y;

	if (!PyArg_ParseTuple(args, "dd:NetworkOptimization.closestVertex", &x, &y))
		return NULL;

	CAST_TO(TNetworkOptimization, graph);

	int i;
	double min = 100000000;
	int ndx = -1;
	for (i=0; i < graph->nVertices; i++)
	{
		double dX = graph->pos[i][0] - x;
		double dY = graph->pos[i][1] - y;
		double d = dX*dX + dY*dY;

		if (d < min)
		{
			min = d;
			ndx = i;
		}
	}

	return Py_BuildValue("id", ndx, sqrt(min));
}

PyObject *NetworkOptimization_random(PyObject *self, PyObject *args) PYARGS(METH_VARARGS, "() -> None")
{
	CAST_TO(TNetworkOptimization, graph);

	graph->random();
	
	RETURN_NONE;
}

WRAPPER(ExampleTable)

PyObject *readNetwork(PyObject *, PyObject *args) PYARGS(METH_VARARGS, "(fn) -> Graph")
{
	TGraph *graph;
	PGraph wgraph;
	TDomain *domain = new TDomain();
	PDomain wdomain = domain;
	TExampleTable *table;
	PExampleTable wtable;

	//cout << "readNetwork" << endl;
	char *fn;

	if (!PyArg_ParseTuple(args, "s:orangeom.readNetwork", &fn))
		return NULL;

	//cout << "File: " << fn << endl;

	string line;
	ifstream file(fn);
	string graphName = "";
	int nVertices = 0;

	if (file.is_open())
	{
		// read head
		while (!file.eof())
		{
			getline (file, line);
			vector<string> words;
			int n = getWords(line, words);
			//cout << line << "  -  " << n << endl;
			if (n > 0)
			{
				if (stricmp(words[0].c_str(), "*network") == 0)
				{
					//cout << "Network" << endl;
					if (n > 1)
					{
						graphName = words[1];
						//cout << "Graph name: " << graphName << endl;
					}
					else
					{
						file.close();
						PYERROR(PyExc_SystemError, "invalid file format", NULL);
					}
				}
				else if (stricmp(words[0].c_str(), "*vertices") == 0)
				{
					//cout << "Vertices" << endl;
					if (n > 1)
					{
						istringstream strVertices(words[1]);
						strVertices >> nVertices;
						if (nVertices == 0)
						{
							file.close();
							PYERROR(PyExc_SystemError, "invalid file format", NULL);
						}

						//cout << "nVertices: " << nVertices << endl;
					}
					else
					{
						file.close();
						PYERROR(PyExc_SystemError, "invalid file format", NULL);
					}

					break;
				}
			}
		}
		graph = new TGraphAsList(nVertices, 0, false);
		wgraph = graph;

		domain->addVariable(new TIntVariable("index"));
		domain->addVariable(new TStringVariable("label"));
		domain->addVariable(new TFloatVariable("x"));
		domain->addVariable(new TFloatVariable("y"));
		domain->addVariable(new TFloatVariable("z"));
		domain->addVariable(new TStringVariable("ic"));
		domain->addVariable(new TStringVariable("bc"));
		domain->addVariable(new TStringVariable("bw"));
		table = new TExampleTable(domain);
  		wtable = table;

		// read vertex descriptions
		while (!file.eof())
		{
			getline (file, line);
			vector<string> words;
			int n = getWords(line, words);
			//cout << line << "  -  " << n << endl;
			if (n > 0)
			{
				TExample *example = new TExample(domain);

				if ((stricmp(words[0].c_str(), "*arcs") == 0) || (stricmp(words[0].c_str(), "*edges") == 0))
					break;

				int index = -1;
				istringstream strIndex(words[0]);
				strIndex >> index;
				if ((index <= 0) || (index > nVertices))
				{
					file.close();
					PYERROR(PyExc_SystemError, "invalid file format", NULL);
				}

				//cout << "index: " << index << " n: " << n << endl;
				(*example)[0] = TValue(index);

				if (n > 1)
				{
					string label = words[1];
					//cout << "label: " << label << endl;
					(*example)[1] = TValue(new TStringValue(label), STRINGVAR);

					int i = 2;
					char *xyz = "  xyz";
					// read coordinates
					while ((i <= 4) && (i < n))
					{
						float coor = -1;	
						istringstream strCoor(words[i]);
						strCoor >> coor;
						
						if ((coor < 0) || (coor > 1))
							break;
						
						//cout << xyz[i] << ": " << coor * 1000 << endl;
						(*example)[i] = TValue(coor);
						i++;
					}
					// read attributes
					while (i < n)
					{
						if (stricmp(words[i].c_str(), "ic") == 0)
						{
							if (i + 1 < n) 
								i++; 
							else 
							{
								file.close();
								PYERROR(PyExc_SystemError, "invalid file format", NULL);
							}

							//cout << "ic: " << words[i] << endl;
							(*example)[5] = TValue(new TStringValue(words[i]), STRINGVAR);
						}
						else if (stricmp(words[i].c_str(), "bc") == 0)
						{
							if (i + 1 < n) 
								i++; 
							else 
							{
								file.close();
								PYERROR(PyExc_SystemError, "invalid file format", NULL);
							}

							//cout << "bc: " << words[i] << endl;
							(*example)[6] = TValue(new TStringValue(words[i]), STRINGVAR);
						}
						else if (stricmp(words[i].c_str(), "bw") == 0)
						{
							if (i + 1 < n) 
								i++; 
							else
							{
								file.close();
								PYERROR(PyExc_SystemError, "invalid file format", NULL);
							}

							//cout << "bw: " << words[i] << endl;
							(*example)[7] = TValue(new TStringValue(words[i]), STRINGVAR);
						}
						i++;
					}
					table->push_back(example);
				}
			}
		}
		// read arcs
		vector<string> words;
		int n = getWords(line, words);
		if (n > 0)
		{
			if (stricmp(words[0].c_str(), "*arcs") == 0)
			{
				while (!file.eof())
				{
					getline (file, line);
					vector<string> words;
					int n = getWords(line, words);
					//cout << line << "  -  " << n << endl;
					if (n > 0)
					{
						if (stricmp(words[0].c_str(), "*edges") == 0)
							break;

						if (n > 1)
						{
							int i1 = -1;
							int i2 = -1;
							istringstream strI1(words[0]);
							istringstream strI2(words[1]);

							strI1 >> i1;
							strI2 >> i2;

							if ((i1 <= 0) || (i1 > nVertices) || (i2 <= 0) || (i2 > nVertices))
							{
								file.close();
								PYERROR(PyExc_SystemError, "invalid file format", NULL);
							}

							if (i1 == i2)
								continue;
							
							//cout << "i1: " << i1 << " i2: " << i2 << endl;
							*graph->getOrCreateEdge(i1 - 1, i2 - 1) = 1;
						}
					}
				}
			}
		}
		// read edges
		n = getWords(line, words);
		if (n > 0)
		{
			if (stricmp(words[0].c_str(), "*edges") == 0)
			{
				while (!file.eof())
				{
					getline (file, line);
					vector<string> words;
					int n = getWords(line, words);
					//cout << line << "  -  " << n << endl;
					if (n > 1)
					{
						int i1 = -1;
						int i2 = -1;
						istringstream strI1(words[0]);
						istringstream strI2(words[1]);

						strI1 >> i1;
						strI2 >> i2;

						if ((i1 <= 0) || (i1 > nVertices) || (i2 <= 0) || (i2 > nVertices))
						{
							file.close();
							PYERROR(PyExc_SystemError, "invalid file format", NULL);
						}

						if (i1 == i2)
							continue;

						*graph->getOrCreateEdge(i1 - 1, i2 - 1) = 1;
						*graph->getOrCreateEdge(i2 - 1, i1 - 1) = 1;
					}
				}
			}
		}

		file.close();
	}
	else
	{
	  PyErr_Format(PyExc_SystemError, "unable to open file '%s'", fn);
	  return NULL;
	}
	
	//graph->setProperty("items", wtable);

	return Py_BuildValue("NN", WrapOrange(wgraph), WrapOrange(wtable));
}

#include "networkoptimization.px"