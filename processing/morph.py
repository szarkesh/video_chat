from cv2 import transform
import numpy as np
from scipy.spatial import Delaunay
import cv2
import helpers_cv2
import face_utils
import math


'''
Helper Function - Do Not Modify
You can use this function in your code
'''

delaunay_triangulation = None

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


def ImageMorphingTriangulation(full_im1, full_im1_pts, full_im2_pts, warp_frac, background_frame, use_all_landmarks = True):
    """
    warps image 1 based on image 2's points. usually warp frac is 1 and dissolve frac is 0
    """
    if not use_all_landmarks:
        full_im1_pts = full_im1_pts[face_utils.LANDMARK_SUBSET]
        full_im2_pts = full_im2_pts[face_utils.LANDMARK_SUBSET]
    #im1_pts = np.subtract(full_im1_pts, [im1bounds[0][0],im1bounds[1][0]])
    # print("Full Image Points 1-2:")
    # print(type(full_im1_pts), full_im1_pts.shape)
    # print(type(full_im2_pts), full_im2_pts.shape)
    # print("Full Image 1:")
    
    #M, mask = cv2.findHomography(full_im2_pts, im1_pts)
    #im2_pts = cv2.perspectiveTransform(np.array([full_im2_pts], np.float32), M)[0].astype(int)

    #homography_

    M, mask = cv2.findHomography(full_im1_pts, full_im2_pts)
    transformed_im1_pts = cv2.perspectiveTransform(np.array([full_im1_pts], np.float32), M)[0].astype(int)
    transformed_im1 = cv2.warpPerspective(full_im1, M, (full_im1.shape[1], full_im1.shape[0]))
    # print("Transformed Iamges")
    # print(type(transformed_im1), transformed_im1.shape)
    # print(type(transformed_im1_pts), transformed_im1_pts.shape)
    bounds = [(min(full_im2_pts[:,0]), max(full_im2_pts[:,0])), (min(full_im2_pts[:,1]), max(full_im2_pts[:,1]))]
    # print(bounds)

    cropped_im2_pts = np.subtract(full_im2_pts, [bounds[0][0], bounds[1][0]])
    cropped_im1 = transformed_im1[bounds[1][0]:bounds[1][1],bounds[0][0]:bounds[0][1]]
    
    cropped_im1_pts = np.subtract(transformed_im1_pts, [bounds[0][0], bounds[1][0]])
    # Compute the H,W of the images (same size)
    # print("Cropped Images")
    # print(type(cropped_im1), cropped_im1.shape)
    # print(type(cropped_im1_pts), cropped_im1_pts.shape)
    # print(type(cropped_im2_pts), cropped_im2_pts)
    cropped_im1_pts_with_corners = np.vstack((cropped_im1_pts, np.asarray([[0,0], [0, cropped_im1.shape[0]], [cropped_im1.shape[1], 0], [cropped_im1.shape[1], cropped_im1.shape[0]]])))
    cropped_im2_pts_with_corners = np.vstack((cropped_im2_pts, np.asarray([[0,0], [0, cropped_im1.shape[0]], [cropped_im1.shape[1], 0], [cropped_im1.shape[1], cropped_im1.shape[0]]])))

    size_H = cropped_im1.shape[0]
    size_W = cropped_im1.shape[1]

    # Find the coordinates of the intermediate points
    intermediate_coords = (1 - warp_frac) * cropped_im1_pts_with_corners + warp_frac * cropped_im2_pts_with_corners

    # Generate Triangulation for the intermediate points (Use Delaunay function)
    global delaunay_triangulation
    delaunay_triangulation = Delaunay(intermediate_coords)
    nTri = delaunay_triangulation.simplices.shape[0]

    # Initialize the Triangle Matrices for all the triangles in image
    ABC_Inter_inv_set = np.zeros((nTri, 3, 3))
    ABC_im1_set = np.zeros((nTri, 3, 3))

    # Fill the Triangle Matries
    for ii, element in enumerate(delaunay_triangulation.simplices):
        ABC_Inter_inv_set[ii, :, :] = np.linalg.inv(matrixABC(intermediate_coords, element))
        ABC_im1_set[ii, :, :] = matrixABC(cropped_im1_pts_with_corners, element)
        #ABC_im2_set[ii, :, :] = matrixABC(im2_pts, element)
    #print(size_H, size_W, delaunay_triangulation, ABC_Inter_inv_set, ABC_im1_set, cropped_im1)
    warp_im1 = generate_warp(size_H, size_W, delaunay_triangulation, ABC_Inter_inv_set, ABC_im1_set, cropped_im1)

    dissolved_full = background_frame.copy()
    convex_hull = cv2.convexHull(np.array(cropped_im1_pts, dtype='float32'))
    convex_hull = [convex_hull.reshape(-1,2).astype(int)]
    mask = helpers_cv2.mask_from_contours(cropped_im1, convex_hull)
    center = (int((bounds[0][0] + bounds[0][1]) / 2), int((bounds[1][0] + bounds[1][1]) / 2))
    #print(center)
    dissolved_full = cv2.seamlessClone(warp_im1, dissolved_full, mask, center, cv2.NORMAL_CLONE)
    #dissolved_full[bounds[1][0]:bounds[1][1], bounds[0][0]:bounds[0][1]] = np.where(mask, warp_im1, dissolved_full[bounds[1][0]:bounds[1][1], bounds[0][0]:bounds[0][1]])
    return dissolved_full


# pastes the body from the neutral frame onto the background frame at the given pose
def PasteBody(background_frame, neutral_frame, neutral_pose, neutral_mask, new_pose):

    neutral_pose = neutral_pose#[face_utils.FACE_POSE_SUBSET]
    new_pose = new_pose#[face_utils.FACE_POSE_SUBSET]
    cv2.imshow('2', neutral_mask)
    neutral_masked = cv2.bitwise_and(neutral_frame, neutral_frame, mask=neutral_mask)
    print(np.mean(neutral_mask), 'avg mask size')
    M, mask = cv2.estimateAffine2D(neutral_pose, new_pose)
    a,b,c,d = M[0][0], M[0][1], M[1][0], M[1][1]
    M2 = np.array([[np.sign(a)*math.sqrt(a**2+b**2), 0, M[0][2]], [0, np.sign(d)*math.sqrt(c**2+d**2), M[1][2]]])
    #print(M2)
    center = (int(background_frame.shape[1]/2), int(background_frame.shape[0]/2))
    warped = cv2.warpAffine(neutral_masked, M2, (neutral_frame.shape[1], neutral_frame.shape[0]))
    kernel = np.ones((5, 5), np.float32) / 25
    mask_warped = cv2.warpAffine(neutral_mask, M2, (neutral_frame.shape[1], neutral_frame.shape[0]))
    mask_warped = cv2.GaussianBlur(mask_warped, (21,21), cv2.BORDER_DEFAULT)

    mask_warped_3channel = np.dstack((mask_warped,) * 3)
    cv2.imshow('2', mask_warped * 255)
    return mask_warped_3channel * warped + (1-mask_warped_3channel)*background_frame