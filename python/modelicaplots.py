import matplotlib.pyplot as plt
import scipy.io
import sdf

#mat = scipy.io.loadmat('C:/Users/jsc-tma/Masterarbeit_tma/Modelica/BESMod/working_dir/SFH_HP_HeatDemand.mat')

#SDF method: read datasets of the desired result paths and plot
file = r'C:/Users/jsc-tma/Masterarbeit_tma/Modelica/BESMod/working_dir/SFH_HP_HeatDemand.sdf'
data = sdf.load(file)

# storage temperatures
variables = []
variables.append('hydraulic.distribution.stoBuf.layer[1].T')
for i in range(5, 21, 5):
    variables.append('hydraulic.distribution.stoBuf.layer[' + str(i) + '].T')
#variables = ['electrical.externalElectricalPin1.PElecLoa', 'building.heatPortCon[1].Q_flow']

datasets = []

for variable in variables:
    # convert the Modelica path to an absolute SDF/HDF5 path
    path = '/' + variable.replace('.', '/')
    # read the dataset
    datasets.append(sdf.load(file, path))
figure, ax = plt.subplots()
#for dataset, variable in zip(datasets, variables):
for i, (dataset, variable) in enumerate(zip(datasets, variables)):
    if i == 0:
        label = "Bottom Layer"
    elif i == len(variables) - 1:
        label = "Top Layer"
    else:
        label = None
    ax.plot(dataset.scales[0].data/3600, dataset.data, label=label)
ax.legend()
plt.title('Temperature Profile of the TES layers')
plt.xlabel('Time [h]')
plt.ylabel('Temperature [K]')
plt.grid(True)
plt.show()

# For single Plots: copy result data straight from Dymola
data = """Time [s]	hydraulic.distribution.stoBuf.TTop
0	19,999994
6,096634	20,25091
6,096634	20,25091
172,8	28,103174
345,6	27,775507
518,4	28,03805
600	28,381525
600	28,381525
691,2	28,82699
839,16656	29,530909
839,16656	29,530909
864	29,648188
1036,8	30,456873
1209,6	31,230219
1382,4	31,951502
1555,2	32,57586
1728	32,974358
1800	33,00347
1800	33,00347
1900,8	42,105064
2073,6	41,751854
2246,4	40,561455
2419,2	40,438194
2592	42,997093
2680,4495	45,61889
2680,4495	45,61889
2734,6165	40,62127
2734,6165	40,62127
2764,8	40,15783
2937,6	43,22091
3110,4	45,398705
3143,786	45,64727
3143,786	45,64727
3283,2	46,454277
3456	47,05001
3600	47,476524
3600	47,476524
3628,8	47,27694
3801,6	48,18444
3974,4	49,958916
4089,9512	50,756645
4089,9512	50,756645
4147,2	51,069603
4320	51,741356
4492,8	52,390923
4534,616	52,612236
4534,616	52,612236
4665,6	53,47448
4838,4	54,711205
5011,2	55,752922
5040	55,902245
5040	55,902245
5042,7754	56,091606
5042,7754	56,091606
5057,2085	57,27468
5057,2085	57,27468
5175,306	58,85888
5175,306	58,85888
5184	58,90844
5356,8	59,81756
5529,6	60,874718
5561,7085	61,099724
5561,7085	61,099724
5702,4	62,254723
5875,2	63,990227
5928,678	64,53121
5928,678	64,53121
6048	64,36828
6220,8	64,14968
6240	64,12643
6240	64,12643
6334,616	64,014305
6334,616	64,014305
6393,6	63,946373
6566,4	63,75457
6739,2	63,572014
6912	63,397118
7084,8	63,22872
7200	63,119713
7200	63,119713
7257,6	63,025993
7430,4	62,859367
7603,2	62,698692
7776	62,543327
7948,8	62,392937
8121,6	62,247093
8134,616	62,23629
8134,616	62,23629
8294,4	62,105522
8467,2	61,967796
8640	61,833702
8812,8	61,702965
8985,6	61,57525
9158,4	61,450188
9331,2	61,327507
9504	61,206657
9676,8	61,08703
9849,6	60,967888
9934,616	60,909264
9934,616	60,909264
10022,4	60,848564
10195,2	60,727806
10368	60,604332
10540,8	60,47689
10713,6	60,344017
10800	60,27511
10800	60,27511
10886,4	60,167046
11059,2	60,0028
11232	59,82595
11404,8	59,6336
11577,6	59,42199
11734,616	59,210625
11734,616	59,210625
11750,4	59,18844
11923,2	58,93151
12096	58,646996
12268,8	58,33178
12441,6	57,984093
12614,4	57,60235
12787,2	57,183983
12960	56,72814
13132,8	56,233543
13305,6	55,699272
13478,4	55,12542
13534,616	54,9302
13534,616	54,9302
13651,2	54,511314
13824	53,85723
13996,8	53,164574
14169,6	52,434868
14342,4	51,668846
14400	51,405663
14400	51,405663
14515,2	50,68627
14688	49,809807
14860,8	48,90841
15033,6	47,98391
15206,4	47,037224
15334,616	46,32415
15334,616	46,32415
15379,2	46,07305
15552	45,089134
15567,559	44,999992
15567,559	44,999992
15572,095	47,11077
15572,095	47,11077
15573,134	47,41204
15573,134	47,41204
15596,94	42,560844
15596,94	42,560844
15724,8	40,045525
15897,6	40,699577
16070,4	44,553062
16154,607	47,66079
16154,607	47,66079
16196,94	49,264397
16196,94	49,264397
16243,2	50,90664
16301,754	52,68676
16301,754	52,68676
16416	48,29949
16588,8	49,527702
16761,6	51,950645
16934,4	55,127403
17107,2	56,853264
17280	57,68435
17379,969	58,42028
17379,969	58,42028
17396,94	58,577873
17396,94	58,577873
17452,8	59,159996
17501,754	59,73629
17501,754	59,73629
17571,57	60,62667
17571,57	60,62667
17625,6	61,3319
17798,4	63,346092
17944,29	64,63271
17944,29	64,63271
17971,2	64,610344
18000	64,5866
18000	64,5866
18144	64,46627
18316,8	64,33187
18489,6	64,20129
18662,4	64,073204
18835,2	63,94668
19008	63,820885
19180,8	63,695274
19196,94	63,683556
19196,94	63,683556
19353,6	63,56951
19526,4	63,44335
19699,2	63,316704
19872	63,189507
20044,8	63,0617
20217,6	62,93325
20390,4	62,804283
20563,2	62,674797
20736	62,544853
20908,8	62,414604
20996,94	62,348045
20996,94	62,348045
21081,6	62,28408
21254,4	62,153404
21427,2	62,022697
21600	61,89193
21600	61,89193
21772,8	61,760918
21945,6	61,630302
22118,4	61,49984
22291,2	61,36947
22464	61,23916
22636,8	61,108818
22796,94	60,987785
22796,94	60,987785
22809,6	60,978203
22982,4	60,84722
23155,2	60,715263
23328	60,581993
23500,8	60,44683
23673,6	60,309166
23846,4	60,168144
24019,2	60,02276
24192	59,872215
24364,8	59,715202
24537,6	59,550407
24596,94	59,491814
24596,94	59,491814
24710,4	59,3767
24883,2	59,19201
25056	58,99456
25200	58,81945
25200	58,81945
25200,203	58,8005
25200,203	58,8005
25228,8	57,53646
25321	56,981987
25321	56,981987
25401,6	56,874474
25500	56,737907
25500	56,737907
25574,4	55,957756
25747,2	53,084923
25902	49,74346
25902	49,74346
25920	49,68966
26092,8	49,161797
26265,6	48,613457
26396,94	48,183006
26396,94	48,183006
26438,4	48,0447
26611,2	47,456047
26784	46,848167
26956,8	46,221886
27000	46,062553
27000	46,062553
27114,594	44,999992
27114,594	44,999992
27119,004	47,014763
27119,004	47,014763
27119,951	47,273888
27119,951	47,273888
27121	47,467583
27121	47,467583
27129,6	46,21093
27134,55	44,357384
27134,55	44,357384
27302,4	35,901665
27475,2	38,773674
27648	45,51104
27734,55	48,96856
27734,55	48,96856
27747,676	49,419548
27747,676	49,419548
27820,8	51,439415
27993,6	53,405174
28132,994	54,45861
28132,994	54,45861
28166,4	51,654472
28339,2	51,707054
28512	56,344994
28567,203	57,61944
28567,203	57,61944
28684,8	59,53353
28800	60,251152
28800	60,251152
28821,887	60,393852
28821,887	60,393852
28857,6	60,93618
28860	60,97616
28860	60,97616
28893,62	60,70574
28893,62	60,70574
28934,55	59,98577
28934,55	59,98577
28957,562	59,389397
28957,562	59,389397
28981	58,86785
28981	58,86785
29009,79	58,551018
29009,79	58,551018
29030,4	58,67257
29129,613	60,24288
29129,613	60,24288
29203,2	61,4627
29332,994	63,63595
29332,994	63,63595
29374,81	64,296104
29374,81	64,296104
29376	64,29482
29548,8	64,11196
29700	63,956413
29700	63,956413
29721,6	63,831932
29821	63,614037
29821	63,614037
29894,4	63,542473
30067,2	63,376396
30240	63,21325
30412,8	63,052727
30585,6	62,894493
30600	62,8814
30600	62,8814
30721	62,70571
30721	62,70571
30734,55	62,693382
30734,55	62,693382
30758,4	62,671715
30931,2	62,51632
31104	62,363518
31276,8	62,21331
31449,6	62,065666
31500	62,023094
31500	62,023094
31621	61,857994
31621	61,857994
31622,4	61,856834
31795,2	61,713554
31968	61,57357
32140,8	61,436882
32313,6	61,30349
32400	61,23803
32400	61,23803
32486,4	60,97695
32521	60,924187
32521	60,924187
32534,55	60,91201
32534,55	60,91201
32659,2	60,802177
32832	60,65557
33004,8	60,51519
33177,6	60,38073
33350,4	60,251823
33523,2	60,128105
33696	60,00918
33868,8	59,894554
34041,6	59,783623
34200	59,684624
34200	59,684624
34214,4	59,68725
34321	59,59823
34321	59,59823
34334,55	59,589806
34334,55	59,589806
34387,2	59,557182
34560	59,45098
34732,8	59,345024
34905,6	59,23806
35078,4	59,128685
35251,2	59,01513
35424	58,89553
35596,8	58,767815
35769,6	58,629845
35942,4	58,479332
36000	58,425987
36000	58,425987
36115,2	58,33007
36134,55	58,310783
36134,55	58,310783
36288	58,149467
36460,8	57,947227
36633,6	57,725517
36806,4	57,480827
36979,2	57,20977
37152	56,908745
37324,8	56,57717
37497,6	56,212975
37670,4	55,81481
37800	55,493187
37800	55,493187
37843,2	55,426292
37860	55,29397
37860	55,29397
37934,55	55,093407
37934,55	55,093407
38016	54,86654
38188,8	54,357964
38361,6	53,811974
38534,4	53,22854
38707,2	52,607872
38880	51,950523
39052,8	51,257347
39225,6	50,529503
39398,4	49,768547
39571,2	48,976585
39600	48,841667
39600	48,841667
39734,55	48,02764
39734,55	48,02764
39744	47,980186
39916,8	47,09411
40089,6	46,185265
40262,4	45,2593
40310,223	44,999992
40310,223	44,999992
40314,76	47,10769
40314,76	47,10769
40315,8	47,407066
40315,8	47,407066
40340,023	42,39785
40340,023	42,39785
40435,2	39,930138
40608	39,96798
40780,8	43,15374
40889,41	47,161217
40889,41	47,161217
40940,023	49,157524
40940,023	49,157524
40953,6	49,673973
41025,066	52,10183
41025,066	52,10183
41126,4	47,835564
41299,2	48,981438
41400	50,051292
41400	50,051292
41472	50,019646
41521	49,94552
41521	49,94552
41644,8	52,707848
41817,6	55,26174
41990,4	56,45144
42140,023	57,498466
42140,023	57,498466
42163,2	57,689262
42225,066	58,257256
42225,066	58,257256
42300	59,062065
42300	59,062065
42336	58,971397
42338,367	58,95559
42338,367	58,95559
42421	58,550163
42421	58,550163
42439,453	58,61541
42439,453	58,61541
42508,8	60,196587
42517,992	60,418785
42517,992	60,418785
42681,6	62,899223
42854,4	64,34521
42896,727	64,65743
42896,727	64,65743
43027,2	64,56417
43200	64,44543
43200	64,44543
43372,8	64,33782
43545,6	64,2264
43718,4	64,11617
43855,945	64,02874
43855,945	64,02874
43891,2	64,00631
43940,023	63,975243
43940,023	63,975243
44064	63,89608
44236,8	63,784904
44409,6	63,672417
44582,4	63,55828
44755,2	63,442314
44928	63,324272
45100,8	63,204094
45273,6	63,081688
45446,4	62,956993
45619,2	62,8301
45740,023	62,740135
45740,023	62,740135
45792	62,701073
45900	62,619408
45900	62,619408
45964,8	62,29635
45990	62,210747
45990	62,210747
46137,6	62,094444
46310,4	61,95742
46483,2	61,81942
46656	61,68035
46800	61,563713
46800	61,563713
46828,8	61,559044
47001,6	61,531548
47054,816	61,523125
47054,816	61,523125
47174,4	61,449486
47347,2	61,33837
47520	61,22628
47540,023	61,21325
47540,023	61,21325
47692,8	61,11315
47865,6	60,998863
48038,4	60,883385
48211,2	60,766624
48384	60,64846
48556,8	60,52871
48729,6	60,407158
48902,4	60,28353
49075,2	60,157494
49248	60,02868
49340,023	59,958794
49340,023	59,958794
49420,8	59,89663
49593,6	59,760735
49766,4	59,620384
49939,2	59,474724
50112	59,323082
50284,8	59,16497
50400	59,05584
50400	59,05584
50457,6	58,782402
50630,4	58,5487
50803,2	58,300316
50976	58,035698
51140,023	57,766563
51140,023	57,766563
51148,8	57,7517
51321,6	57,447105
51494,4	57,11947
51667,2	56,76696
51840	56,388115
52012,8	55,98165
52185,6	55,547325
52200	55,50985
52200	55,50985
52321	55,182426
52321	55,182426
52358,4	55,07885
52531,2	54,5823
52704	54,055687
52876,8	53,49877
52940,023	53,287437
52940,023	53,287437
53049,6	52,911552
53222,4	52,294334
53395,2	51,647728
53568	50,97265
53740,8	50,270042
53913,6	49,540916
54000	49,16677
54000	49,16677
54086,4	49,16091
54259,2	48,490715
54432	47,7716
54604,8	47,036613
54740,023	46,453056
54740,023	46,453056
54777,6	46,2893
54950,4	45,526176
55068,14	44,999992
55068,14	44,999992
55071,555	46,408226
55071,555	46,408226
55072,426	46,613976
55072,426	46,613976
55110,15	38,67553
55110,15	38,67553
55123,2	37,007774
55296	30,992212
55468,8	32,544395
55641,6	37,798637
55668,14	38,6101
55668,14	38,6101
55800	41,142235
55800	41,142235
55814,4	41,42028
55921	39,901115
55921	39,901115
55987,2	39,741753
56160	40,680077
56332,8	42,90017
56378,652	43,67089
56378,652	43,67089
56505,6	45,55813
56678,4	46,938072
56851,2	47,71792
56910,15	48,100426
56910,15	48,100426
56979,902	48,675743
56979,902	48,675743
57024	49,10183
57196,8	50,990105
57369,6	52,6892
57542,4	53,92959
57600	54,307457
57600	54,307457
57715,2	55,647392
57888	56,695946
58060,8	58,24169
58112,605	58,684746
58112,605	58,684746
58233,6	59,23278
58406,4	59,69088
58579,2	60,07766
58638,492	60,19915
58638,492	60,19915
58668,14	60,190453
58668,14	60,190453
58710,15	60,1784
58710,15	60,1784
58752	60,16662
58924,8	60,12063
59097,6	60,078117
59270,4	60,038383
59400	60,00997
59400	60,00997
59443,2	59,302116
59521	59,19744
59521	59,19744
59616	59,176598
59788,8	59,13906
59838,492	59,12835
59838,492	59,12835
59961,6	59,10189
60134,4	59,064842
60307,2	59,027733
60480	58,99047
60510,15	58,98394
60510,15	58,98394
60652,8	58,952934
60825,6	58,915062
60998,4	58,876762
61171,2	58,838036
61200	58,831505
61200	58,831505
61344	58,79165
61516,8	58,74926
61689,6	58,706352
61862,4	58,662865
62035,2	58,618767
62208	58,574028
62310,15	58,547234
62310,15	58,547234
62380,8	58,528557
62553,6	58,482353
62726,4	58,435356
62899,2	58,387474
63072	58,338615
63244,8	58,28872
63417,6	58,237602
63590,4	58,185112
63763,2	58,131004
63936	58,075035
64108,8	58,016808
64110,15	58,01635
64110,15	58,01635
64281,6	57,955986
64454,4	57,891808
64627,2	57,823784
64800	57,75112
64800	57,75112
64921	57,682426
64921	57,682426
64972,8	57,65383
65145,6	57,552788
65318,4	57,441856
65491,2	57,319267
65664	57,18316
65700	57,152916
65700	57,152916
65760	57,028008
65760	57,028008
65836,8	56,95385
65910,15	56,87957
65910,15	56,87957
66009,6	56,773308
66182,4	56,571922
66355,2	56,34762
66528	56,09826
66600	55,986473
66600	55,986473
66660	55,72814
66660	55,72814
66700,8	55,65609
66873,6	55,3323
67046,4	54,97686
67219,2	54,58834
67392	54,16555
67564,8	53,70748
67710,15	53,294518
67710,15	53,294518
67737,6	53,213493
67910,4	52,677635
68083,2	52,109673
68256	51,507713
68400	50,97985
68400	50,97985
68428,8	50,829826
68521	50,087334
68521	50,087334
68601,6	49,752586
68774,4	49,011314
68947,2	48,239555
69120	47,439476
69292,8	46,61358
69465,6	45,764763
69510,15	45,542595
69510,15	45,542595
69617,914	44,999992
69617,914	44,999992
69620,73	46,072258
69620,73	46,072258
69622,1	46,446922
69622,1	46,446922
69638,4	43,65603
69660,9	38,52926
69660,9	38,52926
69811,2	31,131739
69984	31,745203
70156,8	36,611137
70217,914	38,550957
70217,914	38,550957
70329,6	40,876793
70502,4	41,1249
70675,2	40,834618
70848	42,478355
70912,15	43,491783
70912,15	43,491783
71020,8	45,217735
71193,6	47,122124
71366,4	47,91387
71460,9	48,345543
71460,9	48,345543
71485,43	48,49215
71485,43	48,49215
71539,2	48,87368
71712	50,560173
71884,8	52,374413
72000	53,32702
72000	53,32702
72057,6	53,29931
72230,4	54,72448
72403,2	55,9815
72576	57,422447
72748,8	58,759453
72752,83	58,78811
72752,83	58,78811
72921,6	59,372124
73094,4	59,76336
73217,914	60,026237
73217,914	60,026237
73260,9	60,113914
73260,9	60,113914
73267,2	60,12658
73329,77	60,24621
73329,77	60,24621
73440	60,211266
73612,8	60,160698
73785,6	60,11416
73800	60,110435
73800	60,110435
73815,99	59,64486
73815,99	59,64486
73958,4	59,13845
74011	59,054314
74011	59,054314
74131,2	58,996696
74304	58,91738
74476,8	58,841087
74529,77	58,81814
74529,77	58,81814
74649,6	58,766808
74822,4	58,6939
74995,2	58,62191
75060,9	58,59475
75060,9	58,59475
75168	58,55062
75340,8	58,479607
75513,6	58,408592
75600	58,37301
75600	58,37301
75686,4	58,358055
75859,2	58,292564
76032	58,226067
76204,8	58,15853
76377,6	58,089684
76500	58,03994
76500	58,03994
76550,4	58,031975
76621	57,984245
76621	57,984245
76723,2	57,939842
76860,9	57,878746
76860,9	57,878746
76896	57,862938
77068,8	57,783165
77241,6	57,69976
77400	57,61959
77400	57,61959
77414,4	57,60827
77587,2	56,817314
77760	55,389244
77802	54,94448
77802	54,94448
77932,8	54,732384
78105,6	54,43798
78278,4	54,125786
78451,2	53,794456
78624	53,442863
78660,9	53,365074
78660,9	53,365074
78796,8	53,07006
78969,6	52,675102
79142,4	52,257378
79200	52,112938
79200	52,112938
79315,2	52,103783
79438,97	52,0942
79438,97	52,0942
79488	52,006706
79660,8	51,646263
79833,6	51,27105
80006,4	50,880486
80179,2	50,473595
80352	50,050346
80460,9	49,77517
80460,9	49,77517
80524,8	49,61068
80697,6	49,154594
80870,4	48,682213
81043,2	48,19378
81216	47,689415
81388,8	47,169365
81561,6	46,634117
81734,4	46,083916
81907,2	45,519157
82062,39	44,999992
82062,39	44,999992
82065,22	46,078453
82065,22	46,078453
82066,57	46,44445
82066,57	46,44445
82080	44,45971
82100,49	39,061943
82100,49	39,061943
82252,8	30,234766
82425,6	30,548029
82598,4	36,489616
82662,39	38,75289
82662,39	38,75289
82771,2	40,931816
82800	41,115837
82800	41,115837
82944	40,093193
83116,8	39,996178
83289,6	41,656
83432,31	44,039238
83432,31	44,039238
83462,4	44,48681
83635,2	46,24218
83808	46,97616
83900,49	47,411766
83900,49	47,411766
83980,8	47,971764
84092,72	49,02163
84092,72	49,02163
84153,6	49,676292
84326,4	51,456963
84499,2	52,775322
84672	53,835106
84844,8	55,093315
85017,6	56,55709
85190,4	57,93267
85316,734	58,81716
85316,734	58,81716
85363,2	59,03826
85536	59,506218
85662,39	59,796043
85662,39	59,796043
85700,49	59,880913
85700,49	59,880913
85708,8	59,899315
85874,47	60,2362
85874,47	60,2362
85881,6	60,233788
86054,4	60,17904
86227,2	60,129417
86400	60,08364
86400	60,08364"""

# Daten aufbereiten
lines = data.split('\n')[1:]
time = []
temperature = []

for line in lines:
    t, temp = line.split()
    time.append(float(t.replace(',', '.'))/3600)
    temperature.append(float(temp.replace(',', '.')))

# Daten plotten
plt.figure(figsize=(10, 5))
plt.plot(time, temperature, linestyle='-', color='b')
plt.title('Temperature Profile of the Top Layer of Hot Water Storage Tank')
plt.xlabel('Time [h]')
plt.ylabel('Temperature [°C]')
plt.grid(True)
plt.show()
print("Hi")