import numpy as np
from scipy.spatial import Delaunay
import cv2
import time
import scipy
from scipy import signal
from PIL import Image


'''
Helper Function - Do Not Modify
You can use this function in your code
'''


def matrixABC(sparse_control_points, elements):
    """
    Get the triangle matrix given three endpoint sets
    [[ax bx cx]
      [ay by cy]
      [1   1  1]]

    Input -
    sparse_control_points - sparse control points for the input image
    elements - elements (Each Simplex) of Tri.simplices

    Output -
    Stack of all [[ax bx cx]
                  [ay by cy]
                  [1   1  1]]
    """
    output = np.zeros((3, 3))

    # First two rows using Ax Ay Bx By Cx Cy
    for i, element in enumerate(elements):
        output[0:2, i] = sparse_control_points[element, :]

    # Fill last row with 1s
    output[2, :] = 1

    return output


'''
Helper Function - Do Not Modify
You can use this helper function in generate_warp
'''


def interp2(v, xq, yq):
    dim_input = 1
    if len(xq.shape) == 2 or len(yq.shape) == 2:
        dim_input = 2
        q_h = xq.shape[0]
        q_w = xq.shape[1]
        xq = xq.flatten()
        yq = yq.flatten()

    h = v.shape[0]
    w = v.shape[1]
    if xq.shape != yq.shape:
        raise ('query coordinates Xq Yq should have same shape')

    x_floor = np.floor(xq).astype(np.int32)
    y_floor = np.floor(yq).astype(np.int32)
    x_ceil = np.ceil(xq).astype(np.int32)
    y_ceil = np.ceil(yq).astype(np.int32)

    x_floor[x_floor < 0] = 0
    y_floor[y_floor < 0] = 0
    x_ceil[x_ceil < 0] = 0
    y_ceil[y_ceil < 0] = 0

    x_floor[x_floor >= w - 1] = w - 1
    y_floor[y_floor >= h - 1] = h - 1
    x_ceil[x_ceil >= w - 1] = w - 1
    y_ceil[y_ceil >= h - 1] = h - 1

    v1 = v[y_floor, x_floor]
    v2 = v[y_floor, x_ceil]
    v3 = v[y_ceil, x_floor]
    v4 = v[y_ceil, x_ceil]

    lh = yq - y_floor
    lw = xq - x_floor
    hh = 1 - lh
    hw = 1 - lw

    w1 = hh * hw
    w2 = hh * lw
    w3 = lh * hw
    w4 = lh * lw

    interp_val = v1 * w1 + w2 * v2 + w3 * v3 + w4 * v4

    if dim_input == 2:
        return interp_val.reshape(q_h, q_w)
    return interp_val


'''
Function - Modify
'''


def generate_warp(size_H, size_W, Tri, A_Inter_inv_set, A_im_set, image):
    # Generate x,y meshgrid

    # IMPLEMENT HERE

    yy, xx = np.meshgrid(np.arange(0, size_H), np.arange(0, size_W))

    # print(yy)
    # print(xx)
    # Flatten the meshgrid

    positions = np.vstack([xx.ravel(), yy.ravel()])

    # print("positions", xx.shape)

    # IMPLEMENT HERE

    # Zip the flattened x, y and Find Simplices (hint: use list and zip)

    newpos = list(zip(positions[0], positions[1]))
    # print("newpos", newpos)
    tri_idx = Tri.find_simplex(newpos)
    # IMPLEMENT HERE

    # compute alpha, beta, gamma for all the color layers(3)

    bra = A_Inter_inv_set[tri_idx, 0, 0] * positions[0, :] + A_Inter_inv_set[tri_idx, 0, 1] * positions[1, :] + \
          A_Inter_inv_set[tri_idx, 0, 2]
    brb = A_Inter_inv_set[tri_idx, 1, 0] * positions[0, :] + A_Inter_inv_set[tri_idx, 1, 1] * positions[1, :] + \
          A_Inter_inv_set[tri_idx, 1, 2]
    brc = A_Inter_inv_set[tri_idx, 2, 0] * positions[0, :] + A_Inter_inv_set[tri_idx, 2, 1] * positions[1, :] + \
          A_Inter_inv_set[tri_idx, 2, 2]

    # print(bra.shape)
    # print(brb.shape)

    # IMPLEMENT HERE

    # Find all x and y co-ordinates

    px = A_im_set[tri_idx, 0, 0] * bra + A_im_set[tri_idx, 0, 1] * brb + A_im_set[tri_idx, 0, 2] * brc
    py = A_im_set[tri_idx, 1, 0] * bra + A_im_set[tri_idx, 1, 1] * brb + A_im_set[tri_idx, 1, 2] * brc
    pz = A_im_set[tri_idx, 2, 0] * bra + A_im_set[tri_idx, 2, 1] * brb + A_im_set[tri_idx, 2, 2] * brc

    # print('brc is', list(brc))

    # print(px.shape)
    # IMPLEMENT HERE
    # all_z_coor = np.ones(beta.size)

    # Divide all x and y with z

    # IMPLEMENT HERE

    px = px / pz
    py = py / pz

    # Generate Warped Images (Use function interp2) for each of 3 layers
    generated_pic = np.zeros((size_H, size_W, 3), dtype=np.uint8)

    for i in range(0, 3):
        generated_pic[:, :, i] = interp2(image[:, :, i], px.reshape(size_W, size_H),
                                         py.reshape(size_W, size_H)).transpose()

    # IMPLEMENT HERE

    return generated_pic


'''
Function - Do Not Modify
'''


def ImageMorphingTriangulation(full_im1, full_im2, full_im1_pts, full_im2_pts, warp_frac, dissolve_frac):
    """
    warps image 1 based on image 2's points. usually warp frac is 1 and dissolve frac is 0
    """

    im1bounds = [(min(full_im1_pts[:,0]), max(full_im1_pts[:,0])), (min(full_im1_pts[:,1]), max(full_im1_pts[:,1]))]
    im2bounds = [(min(full_im2_pts[:, 0]), max(full_im2_pts[:, 0])), (min(full_im2_pts[:, 1]), max(full_im2_pts[:, 1]))]

    im1 = full_im1[im1bounds[1][0]:im1bounds[1][1], im1bounds[0][0]:im1bounds[0][1]]
    im2 = full_im2[im2bounds[1][0]:im2bounds[1][1], im2bounds[0][0]:im2bounds[0][1]]

    im1_pts = np.subtract(full_im1_pts, [im1bounds[0][0],im1bounds[1][0]])
    im2_pts = np.subtract(full_im2_pts, [im2bounds[0][0],im2bounds[1][0]])

    # Compute the H,W of the images (same size)
    im1_pts = np.vstack((im1_pts, np.asarray([[0,0], [0, im1.shape[0]], [im1.shape[1], 0], [im1.shape[1],im1.shape[0]]])))
    im2_pts = np.vstack((im2_pts, np.asarray([[0,0], [0, im2.shape[0]], [im2.shape[1], 0], [im2.shape[1],im2.shape[0]]])))

    size_H = im1.shape[0]
    size_W = im1.shape[1]

    # Find the coordinates of the intermediate points
    intermediate_coords = (1 - warp_frac) * im1_pts + warp_frac * im2_pts

    # Generate Triangulation for the intermediate points (Use Delaunay function)
    Tri = Delaunay(intermediate_coords)
    nTri = Tri.simplices.shape[0]

    # Initialize the Triangle Matrices for all the triangles in image
    ABC_Inter_inv_set = np.zeros((nTri, 3, 3))
    ABC_im1_set = np.zeros((nTri, 3, 3))
    ABC_im2_set = np.zeros((nTri, 3, 3))

    # Fill the Triangle Matries
    for ii, element in enumerate(Tri.simplices):
        ABC_Inter_inv_set[ii, :, :] = np.linalg.inv(matrixABC(intermediate_coords, element))
        ABC_im1_set[ii, :, :] = matrixABC(im1_pts, element)
        ABC_im2_set[ii, :, :] = matrixABC(im2_pts, element)

    # Generate warp pictures (Use generate warp from the previous block)
    warp_im1 = generate_warp(size_H, size_W, Tri, ABC_Inter_inv_set, ABC_im1_set, im1)
    warp_im2 = generate_warp(size_H, size_W, Tri, ABC_Inter_inv_set, ABC_im2_set, im2)

    # Cross Dissolve
    dissolved_pic = (1 - dissolve_frac) * warp_im1 + dissolve_frac * warp_im2

    # dissolved_pic = dissolved_pic.astype(np.uint8)
    #
    # # Saving each and every image to the folder
    # imgs = Image.fromarray(dissolved_pic, 'RGB')
    # imgs.save('face_morph.png')
    #
    # files.download('face_morph.png')

    dissolved_full = np.copy(full_im1)
    dissolved_full[im1bounds[1][0]:im1bounds[1][1], im1bounds[0][0]:im1bounds[0][1]] = dissolved_pic
    cv2.imshow('1', dissolved_full)
    cv2.imshow('2', full_im2)
    return None